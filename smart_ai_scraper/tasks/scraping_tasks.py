"""
Celery tasks for distributed scraping
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from .celery_app import celery_app
from ..core.scraper import SmartScraper


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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                scraper.scrape(
                    url=url,
                    extractor_type=extractor_type,
                    save_to_db=save_to_db,
                    collection=collection,
                    **kwargs
                )
            )
        finally:
            loop.close()

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
    results = []

    for i, url in enumerate(urls):
        try:
            logger.info(f"Task {self.request.id}: Scraping {i+1}/{len(urls)}: {url}")

            scraper = SmartScraper()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    scraper.scrape(
                        url=url,
                        extractor_type=extractor_type,
                        save_to_db=save_to_db,
                        collection=collection,
                        **kwargs
                    )
                )
                results.append(result)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Task {self.request.id}: Error scraping {url}: {e}")
            results.append({"url": url, "error": str(e)})

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
        threshold: Price change threshold for alerts

    Returns:
        Price monitoring result
    """
    try:
        scraper = SmartScraper()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                scraper.scrape(
                    url=url,
                    extractor_type="product",
                    save_to_db=True,
                    collection=collection,
                )
            )
        finally:
            loop.close()

        # Check price change if threshold provided
        if threshold and result.get("price"):
            from ..storage.database import DatabaseManager

            db = DatabaseManager()
            previous = db.find_one(collection, {"url": url})

            if previous and previous.get("price"):
                old_price = float(previous["price"])
                new_price = float(result["price"])
                change_percent = ((new_price - old_price) / old_price) * 100

                result["price_change"] = change_percent
                result["price_alert"] = abs(change_percent) >= threshold

                logger.info(f"Price change for {url}: {change_percent:.2f}%")

            db.close()

        return result

    except Exception as e:
        logger.error(f"Error monitoring price for {url}: {e}")
        raise
