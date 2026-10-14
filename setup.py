import re
from pathlib import Path

from setuptools import setup, find_packages

version = re.search(
    r'^__version__ = "([^"]+)"',
    Path("smart_ai_scraper/__init__.py").read_text(encoding="utf-8"),
    re.M,
).group(1)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-ai-scraper",
    version=version,
    author="AI Scraper Team",
    description="An AI-powered open-source web scraper with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maidulcu/smart-ai-scraper",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "requests>=2.32.0",
        "spacy>=3.7.2",
        "celery>=5.3.4",
        "redis>=5.0.1",
        "pymongo>=4.6.0",
        "psycopg2-binary>=2.9.9",
        "sqlalchemy>=2.0.23",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
        "fake-useragent>=1.4.0",
        "tenacity>=8.2.3",
        "limits>=3.6.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "loguru>=0.7.2",
    ],
    extras_require={
        # Heavy (multi-GB) and only used when USE_TRANSFORMERS=true
        "transformers": ["transformers>=4.38.0", "torch>=2.1.1"],
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "smart-scraper=smart_ai_scraper.cli:main",
        ],
    },
)
