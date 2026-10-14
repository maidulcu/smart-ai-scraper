"""
Ethical scraping utilities: robots.txt parsing and rate limiting
"""

import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Dict, Optional, Tuple
import asyncio

import requests
from loguru import logger
from limits import RateLimitItemPerMinute, RateLimitItemPerHour
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter

from ..core.config import settings

ROBOTS_USER_AGENT = "smart-ai-scraper"
ROBOTS_FETCH_TIMEOUT = 10  # seconds


class RobotsChecker:
    """Check robots.txt compliance"""

    def __init__(self, cache_ttl: float = 3600):
        # robots.txt URL -> (parser or None when unavailable, fetched_at)
        self._parsers: Dict[str, Tuple[Optional[RobotFileParser], float]] = {}
        self._cache_ttl = cache_ttl

    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _fetch_parser(self, robots_url: str) -> Optional[RobotFileParser]:
        """
        Fetch and parse robots.txt, mirroring RobotFileParser.read() semantics:
        401/403 disallow everything, other 4xx allow everything. Unlike read(),
        this uses a timeout and a descriptive User-Agent (many sites reject the
        default "Python-urllib" agent with a 403, which would block the whole site).
        """
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = requests.get(
                robots_url,
                timeout=ROBOTS_FETCH_TIMEOUT,
                headers={"User-Agent": ROBOTS_USER_AGENT},
            )
        except requests.RequestException as e:
            logger.warning(f"Could not load robots.txt from {robots_url}: {e}")
            return None

        if response.status_code in (401, 403):
            parser.disallow_all = True
        elif 400 <= response.status_code < 500:
            parser.allow_all = True
        elif response.status_code >= 500:
            logger.warning(f"robots.txt at {robots_url} returned {response.status_code}")
            return None
        else:
            parser.parse(response.text.splitlines())
            logger.info(f"Loaded robots.txt from {robots_url}")

        parser.modified()
        return parser

    def _get_parser(self, url: str) -> Optional[RobotFileParser]:
        """Get or create robots.txt parser for a domain"""
        robots_url = self._get_robots_url(url)

        cached = self._parsers.get(robots_url)
        if cached and time.time() - cached[1] < self._cache_ttl:
            return cached[0]

        parser = self._fetch_parser(robots_url)
        self._parsers[robots_url] = (parser, time.time())
        return parser

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if we can fetch a URL according to robots.txt

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            True if allowed, False otherwise
        """
        if not settings.ethical.respect_robots_txt:
            return True

        parser = self._get_parser(url)
        if parser is None:
            # If we can't parse robots.txt, allow by default
            return True

        allowed = parser.can_fetch(user_agent, url)
        if not allowed:
            logger.warning(f"URL blocked by robots.txt: {url}")

        return allowed

    def get_crawl_delay(self, url: str, user_agent: str = "*") -> Optional[float]:
        """
        Get crawl delay specified in robots.txt

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            Crawl delay in seconds, or None if not specified
        """
        if not settings.ethical.respect_robots_txt:
            return None

        parser = self._get_parser(url)
        if parser is None:
            return None

        delay = parser.crawl_delay(user_agent)
        return float(delay) if delay is not None else None


class RateLimiter:
    """Rate limiter for ethical scraping"""

    def __init__(self):
        self.storage = MemoryStorage()
        self.limiter = MovingWindowRateLimiter(self.storage)

        # Define rate limits
        self.per_minute_limit = RateLimitItemPerMinute(settings.rate_limit.requests_per_minute)
        self.per_hour_limit = RateLimitItemPerHour(settings.rate_limit.requests_per_hour)

        # Track last request time per domain
        self._last_request: Dict[str, float] = {}
        # Serialize requests per domain so concurrent tasks can't all pass the
        # limit check or the crawl delay at the same moment
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc

    async def wait_if_needed(self, url: str, crawl_delay: Optional[float] = None):
        """
        Wait if necessary to comply with rate limits

        Args:
            url: URL being accessed
            crawl_delay: Minimum seconds between requests to this domain
                (defaults to the configured crawl delay)
        """
        if not settings.rate_limit.rate_limit_enabled:
            return

        domain = self._get_domain(url)
        delay = settings.ethical.crawl_delay if crawl_delay is None else crawl_delay

        lock = self._locks.setdefault(domain, asyncio.Lock())
        async with lock:
            await self._wait_for_slot(self.per_minute_limit, domain, "per minute", 1)
            await self._wait_for_slot(self.per_hour_limit, domain, "per hour", 60)

            await self.limiter.hit(self.per_minute_limit, domain)
            await self.limiter.hit(self.per_hour_limit, domain)

            # Enforce crawl delay
            if domain in self._last_request:
                elapsed = time.time() - self._last_request[domain]
                if elapsed < delay:
                    wait_time = delay - elapsed
                    logger.debug(f"Crawl delay: waiting {wait_time:.2f}s for {domain}")
                    await asyncio.sleep(wait_time)

            self._last_request[domain] = time.time()

    async def _wait_for_slot(self, limit, domain: str, label: str, poll_interval: float):
        """Block until the given limit has room for one more request"""
        if await self.limiter.test(limit, domain):
            return

        logger.warning(f"Rate limit ({label}) reached for {domain}, waiting...")
        while not await self.limiter.test(limit, domain):
            await asyncio.sleep(poll_interval)

    def reset_domain(self, url: str):
        """Reset rate limiting for a domain"""
        domain = self._get_domain(url)
        if domain in self._last_request:
            del self._last_request[domain]


class EthicalScraper:
    """Combines robots.txt checking and rate limiting"""

    def __init__(self):
        self.robots_checker = RobotsChecker()
        self.rate_limiter = RateLimiter()

    async def can_scrape(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if we can ethically scrape a URL

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            True if allowed, False otherwise
        """
        # robots.txt is fetched with blocking I/O, so keep it off the event loop
        loop = asyncio.get_running_loop()
        allowed = await loop.run_in_executor(
            None, self.robots_checker.can_fetch, url, user_agent
        )
        if not allowed:
            return False

        delay = await loop.run_in_executor(
            None, self.get_recommended_delay, url, user_agent
        )

        # Wait for rate limiting, honoring any robots.txt Crawl-delay
        await self.rate_limiter.wait_if_needed(url, crawl_delay=delay)

        return True

    def get_recommended_delay(self, url: str, user_agent: str = "*") -> float:
        """
        Get recommended crawl delay for a URL

        Args:
            url: URL to check
            user_agent: User agent to check for

        Returns:
            Recommended delay in seconds
        """
        robots_delay = self.robots_checker.get_crawl_delay(url, user_agent)
        config_delay = settings.ethical.crawl_delay

        if robots_delay is not None:
            return max(robots_delay, config_delay)

        return config_delay
