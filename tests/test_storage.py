"""
Tests for storage and configuration helpers that don't need a live database
"""

from urllib.parse import urlparse

import pytest

from smart_ai_scraper.core.config import DatabaseSettings


def test_postgres_url_escapes_credentials():
    db = DatabaseSettings(postgres_user="me", postgres_password="p@ss:w/rd#1")
    parsed = urlparse(db.get_postgres_url())

    assert parsed.hostname == "localhost"
    assert parsed.port == 5432
    assert parsed.path == "/smart_scraper"


def test_scraped_data_model_keeps_metadata_column():
    database = pytest.importorskip("smart_ai_scraper.storage.database")
    if not database.POSTGRES_AVAILABLE:
        pytest.skip("sqlalchemy not installed")

    columns = database.ScrapedData.__table__.columns
    assert "metadata" in columns
    # The declarative MetaData must not be shadowed by the column
    from sqlalchemy import MetaData
    assert isinstance(database.Base.metadata, MetaData)


def test_json_safe_converts_datetimes():
    from datetime import datetime, timezone
    from smart_ai_scraper.storage.database import _json_safe

    value = _json_safe({"at": datetime(2024, 1, 1, tzinfo=timezone.utc), "n": 1})

    assert value == {"at": "2024-01-01 00:00:00+00:00", "n": 1}
