"""
Smart AI Scraper - An AI-powered open-source web scraper
"""

__version__ = "0.1.0"
__author__ = "AI Scraper Team"

from .core.scraper import SmartScraper
from .core.browser import BrowserManager
from .extractors.ai_extractor import AIExtractor

__all__ = ["SmartScraper", "BrowserManager", "AIExtractor"]
