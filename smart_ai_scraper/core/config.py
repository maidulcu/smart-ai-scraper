"""
Configuration management using Pydantic settings
"""

from typing import Optional, List, Literal
from urllib.parse import quote_plus
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class AppSettings(BaseSettings):
    """Application settings"""

    app_name: str = Field(default="smart-ai-scraper", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class BrowserSettings(BaseSettings):
    """Browser configuration"""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_type: Literal["chromium", "firefox", "webkit"] = Field(
        default="chromium", description="Browser type (chromium, firefox, webkit)"
    )
    timeout: int = Field(default=30000, description="Default timeout in milliseconds")
    viewport_width: int = Field(default=1920, description="Viewport width")
    viewport_height: int = Field(default=1080, description="Viewport height")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class AntiBotSettings(BaseSettings):
    """Anti-bot detection settings"""

    min_delay: float = Field(default=1.0, description="Minimum delay between requests (seconds)")
    max_delay: float = Field(default=3.0, description="Maximum delay between requests (seconds)")
    user_agent_rotation: bool = Field(default=True, description="Enable user agent rotation")
    proxy_enabled: bool = Field(default=False, description="Enable proxy support")
    proxy_list: Optional[str] = Field(default=None, description="Comma-separated list of proxies")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_proxy_list(self) -> List[str]:
        """Parse and return proxy list"""
        if self.proxy_list:
            return [p.strip() for p in self.proxy_list.split(",") if p.strip()]
        return []


class RateLimitSettings(BaseSettings):
    """Rate limiting settings"""

    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=10, description="Max requests per minute")
    requests_per_hour: int = Field(default=100, description="Max requests per hour")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class CelerySettings(BaseSettings):
    """Celery configuration"""

    celery_broker_url: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", description="Celery result backend")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    database_type: Literal["mongodb", "postgres"] = Field(
        default="mongodb", description="Database type (mongodb or postgres)"
    )

    # MongoDB settings
    mongodb_uri: str = Field(default="mongodb://localhost:27017/", description="MongoDB URI")
    mongodb_db_name: str = Field(default="smart_scraper", description="MongoDB database name")

    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")
    postgres_db: str = Field(default="smart_scraper", description="PostgreSQL database")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class AISettings(BaseSettings):
    """AI/ML configuration"""

    spacy_model: str = Field(default="en_core_web_sm", description="spaCy model name")
    use_transformers: bool = Field(default=False, description="Use Transformers models")
    transformers_model: str = Field(default="bert-base-uncased", description="Transformers model name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class EthicalScrapingSettings(BaseSettings):
    """Ethical scraping settings"""

    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt")
    crawl_delay: float = Field(default=2.0, description="Crawl delay in seconds")
    max_concurrent_requests: int = Field(default=5, description="Max concurrent requests")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class StorageSettings(BaseSettings):
    """Storage configuration"""

    data_dir: str = Field(default="./data", description="Data directory")
    screenshots_dir: str = Field(default="./screenshots", description="Screenshots directory")
    logs_dir: str = Field(default="./logs", description="Logs directory")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def ensure_directories(self):
        """Create directories if they don't exist"""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.screenshots_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)


class Settings:
    """Main settings class aggregating all configurations"""

    def __init__(self):
        self.app = AppSettings()
        self.browser = BrowserSettings()
        self.anti_bot = AntiBotSettings()
        self.rate_limit = RateLimitSettings()
        self.celery = CelerySettings()
        self.database = DatabaseSettings()
        self.ai = AISettings()
        self.ethical = EthicalScrapingSettings()
        self.storage = StorageSettings()


# Global settings instance
settings = Settings()
