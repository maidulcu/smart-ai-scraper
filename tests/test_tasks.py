"""
Tests for Celery task logic (run synchronously, no broker needed)
"""

import pytest

pytest.importorskip("celery")

from smart_ai_scraper.tasks import scraping_tasks  # noqa: E402


class FakeDB:
    """In-memory stand-in for DatabaseManager"""

    records = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def find(self, collection, query=None, limit=None, newest_first=False):
        rows = [r for r in self.records if r["url"] == query["url"]]
        if newest_first:
            rows = rows[::-1]
        return rows[:limit] if limit else rows


def make_scraper(price, saved):
    class FakeScraper:
        async def scrape(self, url, **kwargs):
            # Simulate the save that happens inside scrape()
            saved.append({"url": url, "price": price})
            return {"url": url, "price": price, "success": True}

    return FakeScraper


@pytest.fixture
def db(monkeypatch):
    FakeDB.records = []
    monkeypatch.setattr(scraping_tasks, "DatabaseManager", FakeDB)
    return FakeDB.records


def test_monitor_price_compares_with_latest_previous(monkeypatch, db):
    db.extend([
        {"url": "https://shop/x", "price": "100"},
        {"url": "https://shop/x", "price": "200"},  # most recent
    ])
    monkeypatch.setattr(scraping_tasks, "SmartScraper", make_scraper("210", db))

    result = scraping_tasks.monitor_price.run("https://shop/x", threshold=10)

    assert result["previous_price"] == 200.0
    assert result["price_change"] == pytest.approx(5.0)
    assert result["price_alert"] is False


def test_monitor_price_first_observation(monkeypatch, db):
    monkeypatch.setattr(scraping_tasks, "SmartScraper", make_scraper("1,299.00", db))

    result = scraping_tasks.monitor_price.run("https://shop/y", threshold=1)

    assert "price_change" not in result


def test_monitor_price_non_numeric_price(monkeypatch, db):
    db.append({"url": "https://shop/z", "price": "Free"})
    monkeypatch.setattr(scraping_tasks, "SmartScraper", make_scraper("12", db))

    result = scraping_tasks.monitor_price.run("https://shop/z", threshold=1)

    assert "price_change" not in result


def test_parse_price():
    assert scraping_tasks._parse_price("1,299.50") == 1299.5
    assert scraping_tasks._parse_price(5) == 5.0
    assert scraping_tasks._parse_price("N/A") is None
    assert scraping_tasks._parse_price(None) is None
