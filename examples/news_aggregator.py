"""
Example: News aggregation and sentiment analysis

This example demonstrates scraping news articles and extracting
entities and structured information.
"""

import asyncio
from smart_ai_scraper import SmartScraper


async def scrape_news_article(url: str):
    """Scrape a single news article"""
    scraper = SmartScraper(headless=True)

    result = await scraper.scrape(
        url=url,
        extractor_type="article",
        save_to_db=True,
        collection="news_articles",
    )

    if result["success"]:
        print(f"Title: {result.get('title')}")
        print(f"Author: {result.get('author')}")
        print(f"Published: {result.get('published_date')}")
        print(f"Entities: {', '.join(result.get('tags', [])[:10])}")
        print(f"Content preview: {result.get('content', '')[:200]}...")
    else:
        print(f"Error: {result.get('error')}")

    return result


async def aggregate_news(news_sites: list):
    """Aggregate news from multiple sources"""
    scraper = SmartScraper(headless=True)

    print(f"Aggregating news from {len(news_sites)} sources...")

    all_articles = []

    for site in news_sites:
        print(f"\nCrawling {site}...")

        # Crawl the news site
        articles = await scraper.crawl(
            start_url=site,
            max_depth=2,
            max_pages=20,
            same_domain_only=True,
            extractor_type="article",
            save_to_db=True,
            collection="news_articles",
        )

        all_articles.extend(articles)
        print(f"Found {len(articles)} articles")

    print(f"\nTotal articles collected: {len(all_articles)}")

    # Analyze entities across all articles
    all_entities = []
    for article in all_articles:
        if "entities" in article:
            all_entities.extend(article["entities"])

    # Count entity mentions
    from collections import Counter

    if all_entities:
        entity_texts = [e["text"] for e in all_entities]
        most_common = Counter(entity_texts).most_common(10)

        print("\nMost mentioned entities:")
        for entity, count in most_common:
            print(f"  {entity}: {count} mentions")

    return all_articles


async def main():
    # Example news site URLs (replace with actual URLs)
    news_sites = [
        "https://example-news.com",
        "https://another-news.com",
    ]

    article_url = "https://example-news.com/article/12345"

    print("News Aggregator Example")
    print("=" * 50)

    # Scrape single article
    # await scrape_news_article(article_url)

    # Aggregate from multiple sources
    # await aggregate_news(news_sites)

    print("\nNote: Replace example URLs with actual news URLs to test")


if __name__ == "__main__":
    asyncio.run(main())
