"""
Tests for ethical scraping utilities
"""

import asyncio
import time

import pytest
import requests

from smart_ai_scraper.core.config import settings
from smart_ai_scraper.utils import ethical
from smart_ai_scraper.utils.ethical import RobotsChecker, RateLimiter, EthicalScraper


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


@pytest.fixture
def fake_robots(monkeypatch):
    """Serve robots.txt responses from a dict instead of the network"""
    responses = {}
    calls = []

    def fake_get(url, timeout=None, headers=None):
        calls.append(url)
        response = responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(ethical.requests, "get", fake_get)
    monkeypatch.setattr(settings.ethical, "respect_robots_txt", True)
    return responses, calls


class TestRobotsChecker:
    """Test robots.txt checking"""

    def setup_method(self):
        """Setup test fixtures"""
        self.checker = RobotsChecker()

    def test_get_robots_url(self):
        """Test robots.txt URL generation"""
        url = "https://example.com/some/path"
        robots_url = self.checker._get_robots_url(url)

        assert robots_url == "https://example.com/robots.txt"

    def test_can_fetch_with_disabled_respect(self, monkeypatch):
        """Test fetching when robots.txt respect is disabled"""
        monkeypatch.setattr(settings.ethical, "respect_robots_txt", False)

        assert self.checker.can_fetch("https://example.com/any/path") is True

    def test_rules_and_crawl_delay(self, fake_robots):
        responses, _ = fake_robots
        responses["https://example.com/robots.txt"] = FakeResponse(
            200, "User-agent: *\nDisallow: /private\nCrawl-delay: 5\n"
        )

        assert self.checker.can_fetch("https://example.com/public") is True
        assert self.checker.can_fetch("https://example.com/private/page") is False
        assert self.checker.get_crawl_delay("https://example.com/") == 5.0

    @pytest.mark.parametrize("status, allowed", [(401, False), (403, False), (404, True), (410, True)])
    def test_http_status_semantics(self, fake_robots, status, allowed):
        responses, _ = fake_robots
        responses["https://example.com/robots.txt"] = FakeResponse(status)

        assert self.checker.can_fetch("https://example.com/page") is allowed

    def test_unreachable_robots_allows(self, fake_robots):
        responses, _ = fake_robots
        responses["https://example.com/robots.txt"] = requests.ConnectionError("down")

        assert self.checker.can_fetch("https://example.com/page") is True

    def test_cache_ttl(self, fake_robots):
        responses, calls = fake_robots
        responses["https://example.com/robots.txt"] = FakeResponse(200, "User-agent: *\nDisallow:\n")

        self.checker.can_fetch("https://example.com/a")
        self.checker.can_fetch("https://example.com/b")
        assert len(calls) == 1

        self.checker._cache_ttl = 0
        self.checker.can_fetch("https://example.com/c")
        assert len(calls) == 2


class TestRateLimiter:
    """Test rate limiting and crawl delay"""

    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_crawl_delay(self, monkeypatch):
        """Concurrent requests to one domain must be spaced by the crawl delay"""
        monkeypatch.setattr(settings.rate_limit, "rate_limit_enabled", True)
        limiter = RateLimiter()
        stamps = []

        async def request():
            await limiter.wait_if_needed("https://example.com/page", crawl_delay=0.2)
            stamps.append(time.monotonic())

        await asyncio.gather(request(), request(), request())

        stamps.sort()
        gaps = [b - a for a, b in zip(stamps, stamps[1:])]
        assert all(gap >= 0.18 for gap in gaps), gaps

    @pytest.mark.asyncio
    async def test_robots_crawl_delay_is_used(self, monkeypatch):
        """EthicalScraper passes the larger of robots.txt and configured delay"""
        monkeypatch.setattr(settings.ethical, "crawl_delay", 1.0)
        scraper = EthicalScraper()
        monkeypatch.setattr(scraper.robots_checker, "can_fetch", lambda url, ua="*": True)
        monkeypatch.setattr(scraper.robots_checker, "get_crawl_delay", lambda url, ua="*": 7.0)

        received = {}

        async def fake_wait(url, crawl_delay=None):
            received["delay"] = crawl_delay

        monkeypatch.setattr(scraper.rate_limiter, "wait_if_needed", fake_wait)

        assert await scraper.can_scrape("https://example.com/") is True
        assert received["delay"] == 7.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
