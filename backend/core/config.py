from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpinionFlow"
    DEBUG: bool = True

    # Bright Data Settings
    BRIGHT_DATA_API_KEY: str
    BRIGHT_DATA_USERNAME: str
    BRIGHT_DATA_PASSWORD: str
    BRIGHT_DATA_SERP_ZONE: str = "opinionflow_serp"
    BRIGHT_DATA_BROWSER_ZONE: str = "opinionflow_browser"

    # Scraping Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    MAX_PRODUCTS_PER_STORE: int = 3
    REQUEST_TIMEOUT: int = 30

    # History Settings
    MAX_HISTORY_ITEMS: int = 50

    # Rate Limiting
    RATE_LIMIT_SECONDS: int = 1
    MAX_REQUESTS_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
