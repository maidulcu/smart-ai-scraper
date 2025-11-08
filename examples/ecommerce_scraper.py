"""
Example: E-commerce price monitoring scraper

This example demonstrates scraping product information from e-commerce sites
and monitoring price changes.
"""

import asyncio
from smart_ai_scraper import SmartScraper


async def scrape_product(url: str):
    """Scrape a single product"""
    scraper = SmartScraper(headless=True)

    result = await scraper.scrape(
        url=url,
        extractor_type="product",
        save_to_db=True,
        collection="products",
        take_screenshot=True,
    )

    if result["success"]:
        print(f"Product: {result.get('name')}")
        print(f"Price: {result.get('currency', '')} {result.get('price')}")
        print(f"Availability: {result.get('availability')}")
        print(f"Description: {result.get('description', '')[:100]}...")
    else:
        print(f"Error: {result.get('error')}")

    return result


async def monitor_prices(urls: list):
    """Monitor prices for multiple products"""
    scraper = SmartScraper(headless=True)

    print(f"Monitoring {len(urls)} products...")

    results = await scraper.scrape_multiple(
        urls=urls,
        extractor_type="product",
        save_to_db=True,
        collection="price_monitoring",
        max_concurrent=3,
    )

    for result in results:
        if result["success"]:
            print(f"\n{result.get('url')}")
            print(f"  Name: {result.get('name')}")
            print(f"  Price: {result.get('currency', '')} {result.get('price')}")
        else:
            print(f"\n{result.get('url')}")
            print(f"  Error: {result.get('error')}")

    return results


async def main():
    # Example product URLs (replace with actual URLs)
    product_urls = [
        "https://example-shop.com/product1",
        "https://example-shop.com/product2",
        # Add more URLs
    ]

    print("E-commerce Scraper Example")
    print("=" * 50)

    # Scrape single product
    # await scrape_product(product_urls[0])

    # Monitor multiple products
    # await monitor_prices(product_urls)

    print("\nNote: Replace example URLs with actual product URLs to test")


if __name__ == "__main__":
    asyncio.run(main())
