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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
