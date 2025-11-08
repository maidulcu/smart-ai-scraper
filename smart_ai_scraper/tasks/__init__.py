"""Celery tasks for distributed scraping"""

from .celery_app import celery_app
from .scraping_tasks import scrape_url, scrape_urls_batch, monitor_price

__all__ = ["celery_app", "scrape_url", "scrape_urls_batch", "monitor_price"]
