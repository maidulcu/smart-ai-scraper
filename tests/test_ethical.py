"""
Tests for ethical scraping utilities
"""

import pytest
from smart_ai_scraper.utils.ethical import RobotsChecker


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

    def test_can_fetch_with_disabled_respect(self):
        """Test fetching when robots.txt respect is disabled"""
        from smart_ai_scraper.core.config import settings

        # Temporarily disable robots.txt respect
        original = settings.ethical.respect_robots_txt
        settings.ethical.respect_robots_txt = False

        result = self.checker.can_fetch("https://example.com/any/path")
        assert result is True

        # Restore original setting
        settings.ethical.respect_robots_txt = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
