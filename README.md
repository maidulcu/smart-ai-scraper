# Smart AI Scraper

An AI-powered open-source web scraper with advanced features for handling dynamic content, anti-bot measures, and intelligent data extraction.

## Features

- **AI-Powered Parsing**: Uses machine learning (spaCy, Transformers) to understand and adapt to different website structures
- **Dynamic Content Handling**: Headless browser (Playwright) support for JavaScript-heavy sites
- **Anti-Bot Bypass**: Mimics human behavior with random delays, mouse movements, and user agent rotation
- **Intelligent Data Extraction**: NLP-powered extraction for products, articles, and general content
- **Scalability**: Distributed scraping with Celery and Redis
- **Ethical Scraping**: Respects robots.txt, implements rate limiting, and crawl delays
- **Multiple Storage Backends**: Supports MongoDB and PostgreSQL
- **Rich CLI**: User-friendly command-line interface with progress indicators

## Tech Stack

- **Backend**: Python 3.8+
- **Headless Browser**: Playwright (Chromium, Firefox, WebKit)
- **AI/ML**: spaCy for NER, optional Transformers support
- **Task Queue**: Celery with Redis
- **Storage**: MongoDB or PostgreSQL
- **CLI**: Click with Rich for beautiful terminal output

## Installation

### Prerequisites

- Python 3.8 or higher
- Redis (for distributed scraping)
- MongoDB or PostgreSQL (for data storage)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-ai-scraper.git
cd smart-ai-scraper

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Run setup assistant
smart-scraper setup
```

### Manual Setup

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Playwright browsers**:
```bash
playwright install chromium
```

3. **Download spaCy model**:
```bash
python -m spacy download en_core_web_sm
```

4. **Configure environment** (create `.env` file):
```bash
cp config/default.env .env
# Edit .env with your settings
```

## Quick Start

### Basic Scraping

Scrape a single URL:
```bash
smart-scraper scrape https://example.com
```

Scrape with product extraction:
```bash
smart-scraper scrape https://shop.com/product --type product --save
```

### Multiple URLs

```bash
smart-scraper scrape-multiple url1 url2 url3 --type article --save
```

### Web Crawling

```bash
smart-scraper crawl https://example.com --depth 2 --max-pages 50
```

### Query Scraped Data

```bash
smart-scraper query scraped_data --limit 10
```

## Usage Examples

### Python API

#### Simple Scraping

```python
import asyncio
from smart_ai_scraper import SmartScraper

async def main():
    scraper = SmartScraper(headless=True)

    result = await scraper.scrape(
        url="https://example.com",
        extractor_type="general",
        save_to_db=True,
    )

    print(f"Title: {result['title']}")
    print(f"Entities: {result['entities']}")

asyncio.run(main())
```

#### E-commerce Scraping

```python
from smart_ai_scraper import SmartScraper

async def scrape_product():
    scraper = SmartScraper()

    result = await scraper.scrape(
        url="https://shop.com/product",
        extractor_type="product",
        save_to_db=True,
        collection="products",
    )

    print(f"Product: {result['name']}")
    print(f"Price: {result['currency']} {result['price']}")
    print(f"Availability: {result['availability']}")
```

#### News Aggregation

```python
from smart_ai_scraper import SmartScraper

async def aggregate_news():
    scraper = SmartScraper()

    articles = await scraper.crawl(
        start_url="https://news-site.com",
        max_depth=2,
        max_pages=50,
        extractor_type="article",
        save_to_db=True,
    )

    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Author: {article['author']}")
        print(f"Entities: {article['tags']}")
```

#### Distributed Scraping with Celery

```python
from smart_ai_scraper.tasks.scraping_tasks import scrape_url

# Submit task to Celery
task = scrape_url.delay(
    url="https://example.com",
    extractor_type="general",
    save_to_db=True,
)

# Get result
result = task.get(timeout=300)
print(result)
```

## Configuration

Configuration is managed through environment variables or a `.env` file:

### Browser Settings
```bash
HEADLESS=true
BROWSER_TYPE=chromium  # chromium, firefox, webkit
TIMEOUT=30000
```

### Anti-Bot Settings
```bash
MIN_DELAY=1
MAX_DELAY=3
USER_AGENT_ROTATION=true
PROXY_ENABLED=false
```

### Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
REQUESTS_PER_MINUTE=10
REQUESTS_PER_HOUR=100
```

### Database
```bash
DATABASE_TYPE=mongodb  # mongodb or postgres
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=smart_scraper
```

### Ethical Scraping
```bash
RESPECT_ROBOTS_TXT=true
CRAWL_DELAY=2
MAX_CONCURRENT_REQUESTS=5
```

## Architecture

```
smart-ai-scraper/
├── smart_ai_scraper/
│   ├── core/              # Core scraping logic
│   │   ├── browser.py     # Playwright browser manager
│   │   ├── config.py      # Configuration management
│   │   └── scraper.py     # Main scraper class
│   ├── extractors/        # Data extraction
│   │   └── ai_extractor.py # AI-powered extraction
│   ├── utils/             # Utilities
│   │   └── ethical.py     # Ethical scraping tools
│   ├── storage/           # Data storage
│   │   └── database.py    # Database abstraction
│   ├── tasks/             # Celery tasks
│   │   ├── celery_app.py
│   │   └── scraping_tasks.py
│   └── cli.py             # Command-line interface
├── examples/              # Usage examples
├── tests/                 # Test suite
└── config/               # Configuration files
```

## Distributed Scraping

### Start Redis
```bash
redis-server
```

### Start Celery Worker
```bash
celery -A smart_ai_scraper.tasks.celery_app worker --loglevel=info
```

### Submit Tasks
```python
from smart_ai_scraper.tasks.scraping_tasks import scrape_urls_batch

# Submit batch of URLs
task = scrape_urls_batch.delay(
    urls=["url1", "url2", "url3"],
    save_to_db=True,
)

# Monitor progress
print(f"Task ID: {task.id}")
print(f"Status: {task.state}")

# Get results
results = task.get()
```

## Use Cases

### 1. E-commerce Price Monitoring
Monitor product prices across multiple e-commerce sites and get alerts on price changes.

See: `examples/ecommerce_scraper.py`

### 2. News Aggregation
Collect news articles from various sources and categorize them using NLP.

See: `examples/news_aggregator.py`

### 3. Real Estate Listings
Aggregate real estate listings from multiple websites.

### 4. Social Media Analysis
Scrape social media posts for sentiment analysis.

## Ethical Considerations

This scraper is designed with ethics in mind:

- **Respects robots.txt**: Automatically checks and follows robots.txt rules
- **Rate Limiting**: Prevents server overload with configurable rate limits
- **Crawl Delays**: Implements delays between requests
- **User Identification**: Uses legitimate user agents
- **Terms of Service**: Users must comply with website ToS

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black smart_ai_scraper/
flake8 smart_ai_scraper/
```

### Type Checking
```bash
mypy smart_ai_scraper/
```

## Troubleshooting

### Playwright Installation Issues
```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

### spaCy Model Not Found
```bash
# Download the model
python -m spacy download en_core_web_sm
```

### Database Connection Issues
- Check MongoDB/PostgreSQL is running
- Verify connection strings in `.env`
- Check firewall settings

### Celery Worker Not Starting
- Ensure Redis is running
- Check `CELERY_BROKER_URL` in configuration
- Verify Celery is installed

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational and research purposes. Users are responsible for:

- Complying with website Terms of Service
- Respecting robots.txt and rate limits
- Following applicable laws and regulations
- Not using the tool for malicious purposes

## Support

- Issues: https://github.com/yourusername/smart-ai-scraper/issues
- Documentation: https://github.com/yourusername/smart-ai-scraper/wiki
- Examples: See `examples/` directory

## Roadmap

- [ ] Support for more AI models (GPT-based extraction)
- [ ] Image recognition for CAPTCHA solving
- [ ] JavaScript rendering optimization
- [ ] Cloud deployment guides (AWS, GCP, Azure)
- [ ] Web UI for scraper management
- [ ] More specialized extractors
- [ ] Proxy rotation support
- [ ] Session management
- [ ] Cookie handling improvements

## Acknowledgments

- Playwright team for excellent browser automation
- spaCy for NLP capabilities
- Celery for distributed task processing
- All contributors and users

---

Made with ❤️ by the Smart AI Scraper Team
