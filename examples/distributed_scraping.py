"""
Example: Distributed scraping using Celery

This example demonstrates how to use Celery to distribute scraping tasks
across multiple workers for scalability.

Prerequisites:
1. Install and start Redis: redis-server
2. Start Celery worker: celery -A smart_ai_scraper.tasks.celery_app worker -Q scraping,celery --loglevel=info
"""

from smart_ai_scraper.tasks.scraping_tasks import scrape_url, scrape_urls_batch, monitor_price


def scrape_single_url_async(url: str):
    """
    Submit a single URL scraping task to Celery

    Returns:
        AsyncResult object
    """
    task = scrape_url.delay(
        url=url,
        extractor_type="general",
        save_to_db=True,
        collection="scraped_data",
    )

    print(f"Task submitted: {task.id}")
    print(f"Task state: {task.state}")

    return task


def scrape_batch_async(urls: list):
    """
    Submit a batch of URLs to Celery

    Returns:
        AsyncResult object
    """
    task = scrape_urls_batch.delay(
        urls=urls,
        extractor_type="general",
        save_to_db=True,
        collection="scraped_data",
    )

    print(f"Batch task submitted: {task.id}")
    print(f"Task state: {task.state}")

    return task


def monitor_product_price(url: str, threshold: float = 5.0):
    """
    Monitor product price and get alerts

    Args:
        url: Product URL
        threshold: Price change percentage threshold for alerts
    """
    task = monitor_price.delay(
        url=url,
        collection="price_monitoring",
        threshold=threshold,
    )

    print(f"Price monitoring task submitted: {task.id}")
    return task


def wait_for_result(task, timeout: int = 300):
    """
    Wait for task result

    Args:
        task: AsyncResult object
        timeout: Timeout in seconds
    """
    print(f"Waiting for task {task.id}...")

    try:
        result = task.get(timeout=timeout)
        print(f"Task completed successfully!")
        return result
    except Exception as e:
        print(f"Task failed: {e}")
        return None


def main():
    print("Distributed Scraping Example")
    print("=" * 50)

    # Example 1: Scrape a single URL
    print("\n1. Scraping single URL asynchronously...")
    task1 = scrape_single_url_async("https://example.com")

    # Wait for result
    result1 = wait_for_result(task1)
    if result1:
        print(f"Success: {result1.get('success')}")
        print(f"Title: {result1.get('title')}")

    # Example 2: Scrape multiple URLs in batch
    print("\n2. Scraping batch of URLs...")
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]

    task2 = scrape_batch_async(urls)
    results2 = wait_for_result(task2)

    if results2:
        successful = sum(1 for r in results2 if r.get("success"))
        print(f"Completed: {successful}/{len(results2)} URLs")

    # Example 3: Monitor product price
    print("\n3. Monitoring product price...")
    product_url = "https://example-shop.com/product/123"
    task3 = monitor_product_price(product_url, threshold=5.0)

    result3 = wait_for_result(task3)
    if result3:
        print(f"Product: {result3.get('name')}")
        print(f"Price: {result3.get('price')}")
        if result3.get('price_alert'):
            print(f"⚠️ Price changed by {result3.get('price_change'):.2f}%")

    print("\n" + "=" * 50)
    print("Note: Make sure Redis is running and Celery worker is started")
    print("Start worker: celery -A smart_ai_scraper.tasks.celery_app worker -Q scraping,celery --loglevel=info")


if __name__ == "__main__":
    main()
