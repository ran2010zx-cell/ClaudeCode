"""
Configuration management for the Xiaomi news tracker
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # Database
    database_url: str = Field(
        default="sqlite:///data/xiaomi_news.db",
        description="Database connection URL"
    )

    # Search keywords
    search_keywords: str = Field(
        default="xiaomi,小米,Xiaomi,XIAOMI",
        description="Comma-separated list of keywords to search for"
    )

    # Crawling settings
    crawl_interval_minutes: int = Field(
        default=60,
        description="Interval between crawls in minutes"
    )

    max_items_per_platform: int = Field(
        default=50,
        description="Maximum number of items to fetch per platform per crawl"
    )

    # Platform API credentials
    # Twitter/X
    twitter_api_key: Optional[str] = Field(default=None, description="Twitter API Key")
    twitter_api_secret: Optional[str] = Field(default=None, description="Twitter API Secret")
    twitter_access_token: Optional[str] = Field(default=None, description="Twitter Access Token")
    twitter_access_token_secret: Optional[str] = Field(default=None, description="Twitter Access Token Secret")
    twitter_bearer_token: Optional[str] = Field(default=None, description="Twitter Bearer Token")

    # Weibo (if using API)
    weibo_app_key: Optional[str] = Field(default=None, description="Weibo App Key")
    weibo_app_secret: Optional[str] = Field(default=None, description="Weibo App Secret")
    weibo_access_token: Optional[str] = Field(default=None, description="Weibo Access Token")

    # Email notification settings
    email_enabled: bool = Field(default=False, description="Enable email notifications")
    email_smtp_host: Optional[str] = Field(default="smtp.gmail.com", description="SMTP host")
    email_smtp_port: int = Field(default=587, description="SMTP port")
    email_from: Optional[str] = Field(default=None, description="Sender email address")
    email_password: Optional[str] = Field(default=None, description="Email password or app password")
    email_to: Optional[str] = Field(default=None, description="Recipient email address")

    # Report settings
    report_format: str = Field(
        default="html",
        description="Report format: 'text', 'html', or 'json'"
    )

    report_min_items: int = Field(
        default=1,
        description="Minimum number of new items before sending report"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/xiaomi_tracker.log", description="Log file path")

    # User agent for web scraping
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="User agent string for HTTP requests"
    )

    # Request settings
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    request_delay: float = Field(default=2.0, description="Delay between requests in seconds")

    def get_keywords_list(self) -> list:
        """Get search keywords as a list"""
        return [k.strip() for k in self.search_keywords.split(',') if k.strip()]


# Global settings instance
settings = Settings()
