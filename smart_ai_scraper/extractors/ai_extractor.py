"""
AI-powered data extraction using NLP
"""

from typing import List, Dict, Any, Optional, Iterator
from bs4 import BeautifulSoup
import json
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
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available. Install with: pip install transformers")

from ..core.config import settings

# spaCy refuses texts longer than nlp.max_length (1,000,000 chars by default),
# and transformer pipelines are slow on long inputs, so cap what we send to NER.
MAX_NER_TEXT_LENGTH = 100_000

PRICE_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")
CURRENCY_PATTERN = re.compile(r"[£$€¥₹]")


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
        text = text[:MAX_NER_TEXT_LENGTH]

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

        # Structured data lives in <script> tags, so read it before stripping them
        structured_data = self._extract_structured_data(soup)
        title = soup.title.get_text(strip=True) if soup.title else None

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

        return {
            "text": text,
            "metadata": metadata,
            "entities": entities,
            "structured_data": structured_data,
            "title": title,
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
        for data in self._load_json_ld(soup):
            structured.append({
                "type": "json-ld",
                "data": data,
            })

        return structured

    @staticmethod
    def _load_json_ld(soup: BeautifulSoup) -> List[Any]:
        """Parse every JSON-LD <script> block, skipping malformed ones"""
        blocks = []
        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            if not raw or not raw.strip():
                continue
            try:
                blocks.append(json.loads(raw))
            except ValueError as e:
                logger.debug(f"Could not parse JSON-LD: {e}")
        return blocks

    @classmethod
    def _iter_json_ld_nodes(cls, data: Any) -> Iterator[Dict[str, Any]]:
        """Yield every JSON-LD object, flattening top-level lists and @graph"""
        if isinstance(data, list):
            for item in data:
                yield from cls._iter_json_ld_nodes(item)
        elif isinstance(data, dict):
            yield data
            if "@graph" in data:
                yield from cls._iter_json_ld_nodes(data["@graph"])

    @staticmethod
    def _has_type(node: Dict[str, Any], *types: str) -> bool:
        """Check a JSON-LD node's @type, which may be a string or a list"""
        node_type = node.get("@type")
        if isinstance(node_type, list):
            return any(t in types for t in node_type)
        return node_type in types

    @staticmethod
    def _first(value: Any) -> Any:
        """Return the first element of a list, or the value itself"""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @classmethod
    def _name_of(cls, value: Any) -> Optional[str]:
        """Read a name from a JSON-LD value that may be a string, object or list"""
        value = cls._first(value)
        if isinstance(value, dict):
            return value.get("name")
        if isinstance(value, str):
            return value
        return None

    @classmethod
    def _url_of(cls, value: Any) -> Optional[str]:
        """Read a URL from a JSON-LD image value (string, ImageObject or list)"""
        value = cls._first(value)
        if isinstance(value, dict):
            return value.get("url") or value.get("contentUrl")
        if isinstance(value, str):
            return value
        return None

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
        for block in self._load_json_ld(soup):
            for node in self._iter_json_ld_nodes(block):
                if not self._has_type(node, "Product"):
                    continue

                product_info["name"] = node.get("name")
                product_info["description"] = node.get("description")
                product_info["image"] = self._url_of(node.get("image"))
                product_info["brand"] = self._name_of(node.get("brand"))

                offers = self._first(node.get("offers"))
                if isinstance(offers, dict):
                    # AggregateOffer uses lowPrice instead of price
                    price = offers.get("price", offers.get("lowPrice"))
                    product_info["price"] = str(price) if price is not None else None
                    product_info["currency"] = offers.get("priceCurrency")
                    product_info["availability"] = offers.get("availability")

                rating = node.get("aggregateRating")
                if isinstance(rating, dict):
                    product_info["rating"] = rating.get("ratingValue")
                break
            if product_info["name"]:
                break

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
                    price_match = PRICE_PATTERN.search(price_text)
                    if not price_match:
                        continue
                    product_info["price"] = price_match.group().replace(',', '')
                    if not product_info["currency"]:
                        currency_match = CURRENCY_PATTERN.search(price_text)
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
        for block in self._load_json_ld(soup):
            for node in self._iter_json_ld_nodes(block):
                if not self._has_type(node, "Article", "NewsArticle", "BlogPosting"):
                    continue

                article_info["title"] = node.get("headline")
                article_info["description"] = node.get("description")
                article_info["published_date"] = node.get("datePublished")
                article_info["modified_date"] = node.get("dateModified")
                article_info["image"] = self._url_of(node.get("image"))
                article_info["author"] = self._name_of(node.get("author"))
                break
            if article_info["title"]:
                break

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
                article_info["tags"] = list(dict.fromkeys(
                    e["text"] for e in entities
                    if e["label"] in ["PERSON", "ORG", "GPE"]
                ))

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
