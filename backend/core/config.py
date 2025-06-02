from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpinionFlow"
    DEBUG: bool = True

    # bright data config
    BRIGHT_DATA_API_KEY: str = ""
    BRIGHT_DATA_SERP_ZONE: str = ""
    BRIGHT_DATA_WEBUNLOCKER_ZONE: str = ""
    
    # Pinecone configuration
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_DISCOVERY_INDEX: str = ""
    PINECONE_REVIEWS_INDEX: str = ""
    
    # other configuration
    CACHE_EXPIRY_DAYS: int = 7
    MAX_PRODUCTS_PER_STORE: int = 5
    GEMINI_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str = ""

    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
