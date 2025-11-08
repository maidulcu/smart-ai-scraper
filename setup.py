from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-ai-scraper",
    version="0.1.0",
    author="AI Scraper Team",
    description="An AI-powered open-source web scraper with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/smart-ai-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "requests>=2.31.0",
        "spacy>=3.7.2",
        "transformers>=4.36.0",
        "torch>=2.1.1",
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
    entry_points={
        "console_scripts": [
            "smart-scraper=smart_ai_scraper.cli:main",
        ],
    },
)
