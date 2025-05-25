from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpinionFlow"
    DEBUG: bool = True


    # bright data base settings
    BRIGHT_DATA_HOST: str = 'brd.superproxy.io'
    BRIGHT_DATA_PORT: int = 33335
    BRIGHT_DATA_API_KEY: str

    # SERP ZONE settings
    BRIGHT_DATA_SERP_USERNAME: str
    BRIGHT_DATA_SERP_PASSWORD: str

    # Web Unlocker settings
    BRIGHT_DATA_WEBUNLOCKER_USERNAME: str
    BRIGHT_DATA_WEBUNLOCKER_PASSWORD: str

    # Browser API settings
    BRIGHT_DATA_BROWSER_API_USERNAME: str
    BRIGHT_DATA_BROWSER_API_PASSWORD: str
    
    # Pinecone configuration
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_DISCOVERY_INDEX: str
    PINECONE_REVIEWS_INDEX: str
    
    # cache configuration
    CACHE_EXPIRY_DAYS: int = 7
    DISCOVERY_SIMILARITY_THRESHOLD: float = 0.85
    
    BRIGHT_DATA_SERP_ZONE: str
    BRIGHT_DATA_WEBUNLOCKER_ZONE: str

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    MAX_PRODUCTS_PER_STORE: int = 3
    MAX_REVIEWS_PER_STORE: int = 100
    REQUEST_TIMEOUT: int = 30

    DATABASE_URL: str

    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    ENABLE_DEBUG_LOGS: bool = False
    MAX_HISTORY_ITEMS: int = 50
    RATE_LIMIT_SECONDS: int = 1
    MAX_REQUESTS_PER_MINUTE: int = 60

    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
