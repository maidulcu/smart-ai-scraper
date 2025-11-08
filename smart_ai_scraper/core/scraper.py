"""
Main Smart Scraper class integrating all components
"""

import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

from .browser import BrowserManager
from .config import settings
from ..extractors.ai_extractor import AIExtractor
from ..utils.ethical import EthicalScraper
from ..storage.database import DatabaseManager


class SmartScraper:
    """
    Main scraper class that integrates all components:
    - Browser automation
    - AI-powered extraction
    - Ethical scraping
    - Data storage
    """

    def __init__(
        self,
        headless: Optional[bool] = None,
        browser_type: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        """
        Initialize Smart Scraper

        Args:
            headless: Run browser in headless mode
            browser_type: Browser type (chromium, firefox, webkit)
            proxy: Proxy server to use
        """
        self.headless = headless
        self.browser_type = browser_type
        self.proxy = proxy

        self.ethical_scraper = EthicalScraper()
        self.extractor = AIExtractor()

    async def scrape(
        self,
        url: str,
        extractor_type: str = "general",
        save_to_db: bool = False,
        collection: str = "scraped_data",
        take_screenshot: bool = False,
        wait_for_selector: Optional[str] = None,
        execute_script: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scrape a URL and extract data

        Args:
            url: URL to scrape
            extractor_type: Type of extraction (general, product, article)
            save_to_db: Whether to save results to database
            collection: Database collection/table name
            take_screenshot: Whether to take a screenshot
            wait_for_selector: CSS selector to wait for before extraction
            execute_script: JavaScript to execute before extraction

        Returns:
            Dictionary with scraped data
        """
        # Check if we can ethically scrape this URL
        can_scrape = await self.ethical_scraper.can_scrape(url)
        if not can_scrape:
            logger.warning(f"Cannot scrape {url} - blocked by robots.txt or rate limit")
            return {
                "url": url,
                "error": "Blocked by ethical scraping rules",
                "success": False,
            }

        result = {
            "url": url,
            "success": False,
        }

        async with BrowserManager(
            headless=self.headless,
            browser_type=self.browser_type,
            proxy=self.proxy,
        ) as browser:
            try:
                # Navigate to URL
                await browser.navigate(url)

                # Wait for selector if specified
                if wait_for_selector:
                    logger.info(f"Waiting for selector: {wait_for_selector}")
                    await browser.wait_for_selector(wait_for_selector)

                # Execute custom script if provided
                if execute_script:
                    logger.info("Executing custom script")
                    await browser.evaluate(execute_script)

                # Get page content
                html = await browser.get_content()

                # Take screenshot if requested
                if take_screenshot:
                    screenshot_path = (
                        Path(settings.storage.screenshots_dir)
                        / f"{self._sanitize_filename(url)}.png"
                    )
                    await browser.screenshot(str(screenshot_path))
                    result["screenshot"] = str(screenshot_path)

                # Extract data based on type
                if extractor_type == "product":
                    extracted_data = self.extractor.extract_product_info(html)
                elif extractor_type == "article":
                    extracted_data = self.extractor.extract_article_info(html)
                else:  # general
                    extracted_data = self.extractor.extract_from_html(html)

                if extracted_data:
                    result.update(extracted_data)
                    result["success"] = True

                # Save to database if requested
                if save_to_db and extracted_data:
                    db = DatabaseManager()
                    try:
                        # Add URL to data
                        extracted_data["url"] = url

                        doc_id = db.save(collection, extracted_data)
                        result["db_id"] = doc_id
                        logger.info(f"Saved to database: {doc_id}")
                    finally:
                        db.close()

                logger.info(f"Successfully scraped {url}")

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                result["error"] = str(e)
                result["success"] = False

        return result

    async def scrape_multiple(
        self,
        urls: List[str],
        extractor_type: str = "general",
        save_to_db: bool = False,
        collection: str = "scraped_data",
        max_concurrent: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently

        Args:
            urls: List of URLs to scrape
            extractor_type: Type of extraction
            save_to_db: Whether to save results to database
            collection: Database collection/table name
            max_concurrent: Maximum concurrent requests

        Returns:
            List of scraped data dictionaries
        """
        max_concurrent = max_concurrent or settings.ethical.max_concurrent_requests

        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape(
                    url=url,
                    extractor_type=extractor_type,
                    save_to_db=save_to_db,
                    collection=collection,
                )

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dictionaries
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": urls[i],
                    "error": str(result),
                    "success": False,
                })
            else:
                processed_results.append(result)

        return processed_results

    async def crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 100,
        same_domain_only: bool = True,
        extractor_type: str = "general",
        save_to_db: bool = False,
        collection: str = "scraped_data",
    ) -> List[Dict[str, Any]]:
        """
        Crawl a website starting from a URL

        Args:
            start_url: Starting URL
            max_depth: Maximum crawl depth
            max_pages: Maximum number of pages to crawl
            same_domain_only: Only crawl links from the same domain
            extractor_type: Type of extraction
            save_to_db: Whether to save results to database
            collection: Database collection/table name

        Returns:
            List of scraped data dictionaries
        """
        from urllib.parse import urlparse, urljoin

        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        results = []

        start_domain = urlparse(start_url).netloc

        async with BrowserManager(
            headless=self.headless,
            browser_type=self.browser_type,
            proxy=self.proxy,
        ) as browser:
            while to_visit and len(visited) < max_pages:
                url, depth = to_visit.pop(0)

                if url in visited:
                    continue

                if depth > max_depth:
                    continue

                # Check domain restriction
                if same_domain_only:
                    if urlparse(url).netloc != start_domain:
                        continue

                # Check if we can scrape
                can_scrape = await self.ethical_scraper.can_scrape(url)
                if not can_scrape:
                    logger.warning(f"Skipping {url} - blocked by ethical rules")
                    continue

                logger.info(f"Crawling ({depth}/{max_depth}): {url}")

                try:
                    # Navigate and extract
                    await browser.navigate(url)
                    html = await browser.get_content()

                    # Extract data
                    if extractor_type == "product":
                        extracted_data = self.extractor.extract_product_info(html)
                    elif extractor_type == "article":
                        extracted_data = self.extractor.extract_article_info(html)
                    else:
                        extracted_data = self.extractor.extract_from_html(html)

                    if extracted_data:
                        extracted_data["url"] = url
                        extracted_data["depth"] = depth
                        results.append(extracted_data)

                        # Save to database if requested
                        if save_to_db:
                            db = DatabaseManager()
                            try:
                                db.save(collection, extracted_data)
                            finally:
                                db.close()

                    # Extract links for further crawling
                    if depth < max_depth:
                        links = await browser.extract_links()
                        for link in links:
                            # Normalize URL
                            absolute_url = urljoin(url, link)

                            if absolute_url not in visited and absolute_url not in [u for u, _ in to_visit]:
                                to_visit.append((absolute_url, depth + 1))

                    visited.add(url)

                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}")
                    visited.add(url)

        logger.info(f"Crawling completed. Visited {len(visited)} pages, extracted {len(results)} items")
        return results

    def _sanitize_filename(self, url: str) -> str:
        """Sanitize URL for use as filename"""
        import re
        from urllib.parse import urlparse

        parsed = urlparse(url)
        filename = f"{parsed.netloc}{parsed.path}".replace("/", "_")
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        return filename[:200]  # Limit length
