"""
Celery tasks for distributed scraping
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from .celery_app import celery_app
from ..core.scraper import SmartScraper
from ..storage.database import DatabaseManager


def _run(coro):
    """Run a coroutine to completion on a fresh event loop (Celery tasks are sync)"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _parse_price(value: Any) -> Optional[float]:
    """Convert a scraped price (str or number) to float, or None if not numeric"""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


@celery_app.task(bind=True, name="smart_ai_scraper.tasks.scraping_tasks.scrape_url")
def scrape_url(
    self,
    url: str,
    extractor_type: str = "general",
    save_to_db: bool = True,
    collection: str = "scraped_data",
    **kwargs
) -> Dict[str, Any]:
    """
    Scrape a single URL

    Args:
        url: URL to scrape
        extractor_type: Type of extractor to use (general, product, article)
        save_to_db: Whether to save results to database
        collection: Database collection name
        **kwargs: Additional arguments for scraper

    Returns:
        Scraped data dictionary
    """
    try:
        logger.info(f"Task {self.request.id}: Scraping {url}")

        # Create scraper and run
        scraper = SmartScraper()

        # Run async scrape in sync context
        result = _run(
            scraper.scrape(
                url=url,
                extractor_type=extractor_type,
                save_to_db=save_to_db,
                collection=collection,
                **kwargs
            )
        )

        logger.info(f"Task {self.request.id}: Successfully scraped {url}")
        return result

    except Exception as e:
        logger.error(f"Task {self.request.id}: Error scraping {url}: {e}")
        raise


@celery_app.task(bind=True, name="smart_ai_scraper.tasks.scraping_tasks.scrape_urls_batch")
def scrape_urls_batch(
    self,
    urls: List[str],
    extractor_type: str = "general",
    save_to_db: bool = True,
    collection: str = "scraped_data",
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Scrape a batch of URLs

    Args:
        urls: List of URLs to scrape
        extractor_type: Type of extractor to use
        save_to_db: Whether to save results to database
        collection: Database collection name
        **kwargs: Additional arguments for scraper

    Returns:
        List of scraped data dictionaries
    """
    # One scraper for the whole batch so rate limits and crawl delays apply
    # across URLs instead of being reset for each one
    scraper = SmartScraper()

    async def run_batch() -> List[Dict[str, Any]]:
        results = []
        for i, url in enumerate(urls):
            try:
                logger.info(f"Task {self.request.id}: Scraping {i+1}/{len(urls)}: {url}")
                results.append(await scraper.scrape(
                    url=url,
                    extractor_type=extractor_type,
                    save_to_db=save_to_db,
                    collection=collection,
                    **kwargs
                ))
            except Exception as e:
                logger.error(f"Task {self.request.id}: Error scraping {url}: {e}")
                results.append({"url": url, "error": str(e), "success": False})
        return results

    results = _run(run_batch())

    logger.info(f"Task {self.request.id}: Completed batch of {len(urls)} URLs")
    return results


@celery_app.task(name="smart_ai_scraper.tasks.scraping_tasks.monitor_price")
def monitor_price(
    url: str,
    collection: str = "price_monitoring",
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Monitor product price changes

    Args:
        url: Product URL to monitor
        collection: Database collection name
        threshold: Price change threshold (percent) for alerts

    Returns:
        Price monitoring result
    """
    try:
        # Look up the most recent observation *before* saving the new one,
        # otherwise we'd compare the new price against itself (or the oldest)
        with DatabaseManager() as db:
            previous_records = db.find(collection, {"url": url}, limit=1, newest_first=True)
        previous = previous_records[0] if previous_records else None

        scraper = SmartScraper()
        result = _run(
            scraper.scrape(
                url=url,
                extractor_type="product",
                save_to_db=True,
                collection=collection,
            )
        )

        old_price = _parse_price(previous.get("price")) if previous else None
        new_price = _parse_price(result.get("price"))

        if old_price and new_price is not None:
            change_percent = ((new_price - old_price) / old_price) * 100
            result["previous_price"] = old_price
            result["price_change"] = change_percent
            if threshold is not None:
                result["price_alert"] = abs(change_percent) >= threshold

            logger.info(f"Price change for {url}: {change_percent:.2f}%")

        return result

    except Exception as e:
        logger.error(f"Error monitoring price for {url}: {e}")
        raise
