"""
Tests for AI Extractor
"""

import pytest
from smart_ai_scraper.extractors.ai_extractor import AIExtractor


class TestAIExtractor:
    """Test AI-powered data extraction"""

    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = AIExtractor(use_transformers=False)

    def test_extract_from_html_basic(self):
        """Test basic HTML extraction"""
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Welcome to Test Page</h1>
                <p>This is a test paragraph.</p>
            </body>
        </html>
        """

        result = self.extractor.extract_from_html(html)

        assert result is not None
        assert result["title"] == "Test Page"
        assert "Test Page" in result["text"]
        assert "description" in result["metadata"]

    def test_extract_product_info(self):
        """Test product information extraction"""
        html = """
        <html>
            <body>
                <h1 class="product-title">Test Product</h1>
                <span class="price">$99.99</span>
                <p class="description">This is a test product</p>
            </body>
        </html>
        """

        result = self.extractor.extract_product_info(html)

        assert result is not None
        assert result["name"] == "Test Product"
        assert "99.99" in str(result["price"])

    def test_extract_article_info(self):
        """Test article information extraction"""
        html = """
        <html>
            <body>
                <article>
                    <h1>Test Article</h1>
                    <p>This is a test article about testing.</p>
                </article>
            </body>
        </html>
        """

        result = self.extractor.extract_article_info(html)

        assert result is not None
        assert result["title"] == "Test Article"
        assert "test article" in result["content"].lower()

    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "This   is    a   test   with   extra    spaces"
        clean = self.extractor.clean_text(dirty_text)

        assert "  " not in clean
        assert clean == "This is a test with extra spaces"

    def test_extract_metadata(self):
        """Test metadata extraction"""
        html = """
        <html>
            <head>
                <meta name="author" content="Test Author">
                <meta property="og:title" content="OG Title">
                <meta name="twitter:card" content="summary">
            </head>
            <body></body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        metadata = self.extractor._extract_metadata(soup)

        assert "author" in metadata
        assert metadata["author"] == "Test Author"
        assert "og:title" in metadata
        assert metadata["og:title"] == "OG Title"

    def test_extract_from_html_keeps_json_ld(self):
        """JSON-LD must be read before <script> tags are stripped"""
        html = """
        <html>
            <head>
                <title>T</title>
                <script type="application/ld+json">{"@type": "Product", "name": "X"}</script>
            </head>
            <body>hi</body>
        </html>
        """

        result = self.extractor.extract_from_html(html)

        assert result["structured_data"] == [
            {"type": "json-ld", "data": {"@type": "Product", "name": "X"}}
        ]
        assert '"@type"' not in result["text"]
        assert isinstance(result["title"], str)

    def test_extract_product_info_json_ld_variants(self):
        """String brand, list of offers, image list and @type list are all valid JSON-LD"""
        html = """
        <script type="application/ld+json">
        {"@type": ["Product", "Thing"], "name": "Widget", "brand": "Acme",
         "image": ["https://example.com/a.jpg"],
         "offers": [{"price": 9.99, "priceCurrency": "USD", "availability": "InStock"}],
         "aggregateRating": {"ratingValue": "4.5"}}
        </script>
        """

        result = self.extractor.extract_product_info(html)

        assert result["name"] == "Widget"
        assert result["brand"] == "Acme"
        assert result["image"] == "https://example.com/a.jpg"
        assert result["price"] == "9.99"
        assert result["currency"] == "USD"
        assert result["availability"] == "InStock"
        assert result["rating"] == "4.5"

    def test_extract_product_info_json_ld_graph(self):
        """Products nested in @graph are found"""
        html = """
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@graph": [
            {"@type": "WebPage", "name": "Page"},
            {"@type": "Product", "name": "Gadget", "brand": {"name": "Acme"},
             "offers": {"@type": "AggregateOffer", "lowPrice": "5", "priceCurrency": "EUR"}}
        ]}
        </script>
        """

        result = self.extractor.extract_product_info(html)

        assert result["name"] == "Gadget"
        assert result["brand"] == "Acme"
        assert result["price"] == "5"
        assert result["currency"] == "EUR"

    def test_extract_product_price_ignores_stray_commas(self):
        """A comma before the number must not be taken as the price"""
        html = '<h1>Item</h1><span class="price">, now $1,299.50</span>'

        result = self.extractor.extract_product_info(html)

        assert result["price"] == "1299.50"
        assert result["currency"] == "$"

    def test_extract_article_info_author_variants(self):
        """Authors may be plain strings, and articles may live in @graph"""
        html = """
        <script type="application/ld+json">
        {"@graph": [{"@type": "NewsArticle", "headline": "Headline",
                     "author": ["Jane Doe"], "image": {"url": "https://example.com/i.png"}}]}
        </script>
        """

        result = self.extractor.extract_article_info(html)

        assert result["title"] == "Headline"
        assert result["author"] == "Jane Doe"
        assert result["image"] == "https://example.com/i.png"

    def test_malformed_json_ld_is_skipped(self):
        """Broken or empty JSON-LD blocks don't hide valid ones"""
        html = """
        <script type="application/ld+json">{not json</script>
        <script type="application/ld+json"></script>
        <script type="application/ld+json">{"@type": "Product", "name": "Ok"}</script>
        """

        result = self.extractor.extract_product_info(html)

        assert result["name"] == "Ok"

    def test_extract_entities_truncates_long_text(self):
        """Very long pages are capped before NER (spaCy rejects > nlp.max_length)"""
        from smart_ai_scraper.extractors.ai_extractor import MAX_NER_TEXT_LENGTH

        seen = {}

        class FakeNLP:
            def __call__(self, text):
                seen["length"] = len(text)

                class Doc:
                    ents = []
                return Doc()

        self.extractor.use_transformers = False
        self.extractor.nlp = FakeNLP()
        self.extractor.extract_entities("a" * (MAX_NER_TEXT_LENGTH + 10))

        assert seen["length"] == MAX_NER_TEXT_LENGTH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
