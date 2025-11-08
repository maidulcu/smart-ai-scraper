"""
Celery application for distributed scraping tasks
"""

from celery import Celery
from ..core.config import settings

# Create Celery app
celery_app = Celery(
    "smart_ai_scraper",
    broker=settings.celery.celery_broker_url,
    backend=settings.celery.celery_result_backend,
    include=["smart_ai_scraper.tasks.scraping_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    "smart_ai_scraper.tasks.scraping_tasks.scrape_url": {"queue": "scraping"},
    "smart_ai_scraper.tasks.scraping_tasks.scrape_urls_batch": {"queue": "scraping"},
}
