"""
AI-powered data extraction using NLP
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from loguru import logger

try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install with: python -m spacy download en_core_web_sm")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Install with: pip install transformers")

from ..core.config import settings


class AIExtractor:
    """AI-powered content extraction using NLP"""

    def __init__(self, use_transformers: Optional[bool] = None):
        self.use_transformers = use_transformers if use_transformers is not None else settings.ai.use_transformers

        self.nlp: Optional[Language] = None
        self.ner_pipeline = None

        self._initialize_models()

    def _initialize_models(self):
        """Initialize NLP models"""
        if self.use_transformers and TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading Transformers model: {settings.ai.transformers_model}")
                self.ner_pipeline = pipeline(
                    "ner",
                    model=settings.ai.transformers_model,
                    aggregation_strategy="simple"
                )
                logger.info("Transformers model loaded successfully")
            except Exception as e:
                logger.error(f"Could not load Transformers model: {e}")
                self.use_transformers = False

        if not self.use_transformers and SPACY_AVAILABLE:
            try:
                logger.info(f"Loading spaCy model: {settings.ai.spacy_model}")
                self.nlp = spacy.load(settings.ai.spacy_model)
                logger.info("spaCy model loaded successfully")
            except Exception as e:
                logger.error(f"Could not load spaCy model: {e}")
                logger.info("Try running: python -m spacy download en_core_web_sm")

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text

        Args:
            text: Text to extract entities from

        Returns:
            List of entities with type and text
        """
        if self.use_transformers and self.ner_pipeline:
            return self._extract_entities_transformers(text)
        elif self.nlp:
            return self._extract_entities_spacy(text)
        else:
            logger.warning("No NLP model available for entity extraction")
            return []

    def _extract_entities_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy"""
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            })

        return entities

    def _extract_entities_transformers(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using Transformers"""
        results = self.ner_pipeline(text)

        entities = []
        for result in results:
            entities.append({
                "text": result["word"],
                "label": result["entity_group"],
                "score": result["score"],
                "start": result["start"],
                "end": result["end"],
            })

        return entities

    def extract_from_html(self, html: str) -> Dict[str, Any]:
        """
        Extract structured data from HTML

        Args:
            html: HTML content

        Returns:
            Dictionary with extracted data
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        # Extract text
        text = soup.get_text(separator=" ", strip=True)

        # Clean up text
        text = re.sub(r'\s+', ' ', text)

        # Extract metadata
        metadata = self._extract_metadata(soup)

        # Extract entities
        entities = self.extract_entities(text)

        # Extract structured data
        structured_data = self._extract_structured_data(soup)

        return {
            "text": text,
            "metadata": metadata,
            "entities": entities,
            "structured_data": structured_data,
            "title": soup.title.string if soup.title else None,
        }

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML"""
        metadata = {}

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        # Open Graph tags
        for meta in soup.find_all("meta", property=re.compile("^og:")):
            prop = meta.get("property")
            content = meta.get("content")
            if prop and content:
                metadata[prop] = content

        # Twitter Card tags
        for meta in soup.find_all("meta", attrs={"name": re.compile("^twitter:")}):
            name = meta.get("name")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        return metadata

    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured data (JSON-LD, microdata, etc.)"""
        structured = []

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)
                structured.append({
                    "type": "json-ld",
                    "data": data,
                })
            except Exception as e:
                logger.debug(f"Could not parse JSON-LD: {e}")

        return structured

    def extract_product_info(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract product information from e-commerce pages

        Args:
            html: HTML content

        Returns:
            Product information dictionary
        """
        soup = BeautifulSoup(html, "lxml")

        product_info = {
            "name": None,
            "price": None,
            "currency": None,
            "description": None,
            "image": None,
            "availability": None,
            "brand": None,
            "rating": None,
        }

        # Try to extract from structured data first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)

                if isinstance(data, dict):
                    if data.get("@type") == "Product":
                        product_info["name"] = data.get("name")
                        product_info["description"] = data.get("description")
                        product_info["image"] = data.get("image")
                        product_info["brand"] = data.get("brand", {}).get("name")

                        offers = data.get("offers", {})
                        if isinstance(offers, dict):
                            product_info["price"] = offers.get("price")
                            product_info["currency"] = offers.get("priceCurrency")
                            product_info["availability"] = offers.get("availability")

                        rating = data.get("aggregateRating", {})
                        if rating:
                            product_info["rating"] = rating.get("ratingValue")

            except Exception as e:
                logger.debug(f"Could not parse product JSON-LD: {e}")

        # Fallback: try to extract from common selectors
        if not product_info["name"]:
            name_selectors = ["h1.product-title", "h1[itemprop='name']", "h1.product-name", "h1"]
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    product_info["name"] = element.get_text(strip=True)
                    break

        if not product_info["price"]:
            price_selectors = [
                "[itemprop='price']",
                ".price",
                ".product-price",
                "[class*='price']"
            ]
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        product_info["price"] = price_match.group().replace(',', '')
                    # Extract currency
                    currency_match = re.search(r'[£$€¥]', price_text)
                    if currency_match:
                        product_info["currency"] = currency_match.group()
                    break

        return product_info if any(product_info.values()) else None

    def extract_article_info(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract article information from news pages

        Args:
            html: HTML content

        Returns:
            Article information dictionary
        """
        soup = BeautifulSoup(html, "lxml")

        article_info = {
            "title": None,
            "author": None,
            "published_date": None,
            "modified_date": None,
            "description": None,
            "content": None,
            "image": None,
            "tags": [],
        }

        # Try structured data first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)

                if isinstance(data, dict):
                    if data.get("@type") in ["Article", "NewsArticle", "BlogPosting"]:
                        article_info["title"] = data.get("headline")
                        article_info["description"] = data.get("description")
                        article_info["published_date"] = data.get("datePublished")
                        article_info["modified_date"] = data.get("dateModified")
                        article_info["image"] = data.get("image")

                        author = data.get("author", {})
                        if isinstance(author, dict):
                            article_info["author"] = author.get("name")
                        elif isinstance(author, list) and author:
                            article_info["author"] = author[0].get("name")

            except Exception as e:
                logger.debug(f"Could not parse article JSON-LD: {e}")

        # Fallback: extract from common selectors
        if not article_info["title"]:
            title_selectors = ["h1.article-title", "h1[itemprop='headline']", "article h1", "h1"]
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    article_info["title"] = element.get_text(strip=True)
                    break

        # Extract main content
        article = soup.find("article") or soup.find("main")
        if article:
            # Remove unwanted elements
            for unwanted in article.find_all(["aside", "nav", "footer", "header"]):
                unwanted.decompose()

            article_info["content"] = article.get_text(separator="\n", strip=True)

            # Extract entities from content
            if article_info["content"]:
                entities = self.extract_entities(article_info["content"])
                # Extract people and organizations as potential tags
                article_info["tags"] = [
                    e["text"] for e in entities
                    if e["label"] in ["PERSON", "ORG", "GPE"]
                ]

        return article_info if any(article_info.values()) else None

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\'\"()]', '', text)

        return text.strip()
