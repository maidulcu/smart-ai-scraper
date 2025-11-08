"""
Ethical scraping utilities: robots.txt parsing and rate limiting
"""

import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

import requests
from loguru import logger
from limits import RateLimitItemPerMinute, RateLimitItemPerHour
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter

from ..core.config import settings


class RobotsChecker:
    """Check robots.txt compliance"""

    def __init__(self):
        self._parsers: Dict[str, RobotFileParser] = {}
        self._cache_ttl = 3600  # Cache for 1 hour

    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _get_parser(self, url: str) -> Optional[RobotFileParser]:
        """Get or create robots.txt parser for a domain"""
        robots_url = self._get_robots_url(url)

        # Check cache
        if robots_url in self._parsers:
            return self._parsers[robots_url]

        # Fetch and parse robots.txt
        try:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.read()
            self._parsers[robots_url] = parser
            logger.info(f"Loaded robots.txt from {robots_url}")
            return parser
        except Exception as e:
            logger.warning(f"Could not load robots.txt from {robots_url}: {e}")
            return None

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
        parser = self._get_parser(url)
        if parser is None:
            return None

        return parser.crawl_delay(user_agent)


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

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc

    async def wait_if_needed(self, url: str):
        """
        Wait if necessary to comply with rate limits

        Args:
            url: URL being accessed
        """
        if not settings.rate_limit.rate_limit_enabled:
            return

        domain = self._get_domain(url)

        # Check rate limits
        if not await self.limiter.test(self.per_minute_limit, domain):
            logger.warning(f"Rate limit (per minute) reached for {domain}, waiting...")
            while not await self.limiter.test(self.per_minute_limit, domain):
                await asyncio.sleep(1)

        if not await self.limiter.test(self.per_hour_limit, domain):
            logger.warning(f"Rate limit (per hour) reached for {domain}, waiting...")
            while not await self.limiter.test(self.per_hour_limit, domain):
                await asyncio.sleep(60)

        # Hit the rate limiter
        await self.limiter.hit(self.per_minute_limit, domain)
        await self.limiter.hit(self.per_hour_limit, domain)

        # Enforce crawl delay
        if domain in self._last_request:
            elapsed = time.time() - self._last_request[domain]
            if elapsed < settings.ethical.crawl_delay:
                wait_time = settings.ethical.crawl_delay - elapsed
                logger.debug(f"Crawl delay: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)

        self._last_request[domain] = time.time()

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
        # Check robots.txt
        if not self.robots_checker.can_fetch(url, user_agent):
            return False

        # Wait for rate limiting
        await self.rate_limiter.wait_if_needed(url)

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
