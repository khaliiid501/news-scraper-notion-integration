"""Configuration management for the news scraper service."""


from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database Configuration
    database_url: str = Field(
        default="postgresql://newsuser:newspass@localhost:5432/newsdb",
        description="PostgreSQL database URL"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")

    # News Sources Configuration
    news_sources: list[str] = Field(
        default=[
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.cnn.com/rss/edition.rss"
        ],
        description="List of RSS feed URLs"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format")

    # Scraper Configuration
    scrape_interval: int = Field(default=3600, description="Scrape interval in seconds")
    max_articles_per_source: int = Field(default=50, description="Maximum articles per source")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
