"""
Tests for SmartScraper helpers
"""

import pytest

from smart_ai_scraper.core.scraper import SmartScraper


class TestNormalizeLink:
    @pytest.mark.parametrize("link, expected", [
        ("/about", "https://example.com/about"),
        ("page#section", "https://example.com/blog/page"),
        ("https://other.com/x#y", "https://other.com/x"),
        ("mailto:me@example.com", None),
        ("javascript:void(0)", None),
        ("tel:+123", None),
    ])
    def test_normalize_link(self, link, expected):
        assert SmartScraper._normalize_link("https://example.com/blog/", link) == expected


def test_sanitize_filename():
    scraper = SmartScraper.__new__(SmartScraper)
    name = scraper._sanitize_filename("https://example.com/a/b?c=d&e=<f>")

    assert name == "example.com_a_b"
    assert "/" not in name
