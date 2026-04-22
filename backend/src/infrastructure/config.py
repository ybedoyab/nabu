"""Configuration for the Research Assistant backend API."""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from settings import settings as global_settings

class Settings:
    """Application settings."""

    # API Configuration
    API_HOST: str = global_settings.API_HOST
    API_PORT: int = global_settings.API_PORT
    API_V1_STR: str = global_settings.API_V1_STR
    PROJECT_NAME: str = global_settings.PROJECT_NAME
    VERSION: str = global_settings.VERSION

    # OpenAI Configuration (sensitive values from env)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", global_settings.OPENAI_API_KEY)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", global_settings.OPENAI_MODEL)
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", str(global_settings.OPENAI_MAX_TOKENS)))
    OPENAI_TEMPERATURE: float = float(
        os.getenv("OPENAI_TEMPERATURE", str(global_settings.OPENAI_TEMPERATURE))
    )

    # CORS Configuration
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*",  # Allow all origins for remote access
    ]

    # Data Configuration
    DATA_DIR: str = global_settings.DATA_DIR_NAME
    OUTPUT_DIR: str = global_settings.OUTPUT_DIR_NAME
    CACHE_DIR: str = global_settings.CACHE_DIR_NAME

    # Processing Configuration
    MAX_CONCURRENT_REQUESTS: int = int(
        os.getenv("MAX_CONCURRENT_REQUESTS", str(global_settings.MAX_CONCURRENT_REQUESTS))
    )
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", str(global_settings.REQUEST_DELAY)))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", str(global_settings.BATCH_SIZE)))

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(
        os.getenv("RATE_LIMIT_PER_MINUTE", str(global_settings.RATE_LIMIT_PER_MINUTE))
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", global_settings.LOG_LEVEL)

    def __init__(self):
        # Keep origin list stable by default for local development.
        pass

# Global settings instance
settings = Settings()

# Validate required settings
def validate_settings() -> bool:
    """Validate that all required settings are present."""
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is required")
        return False
    
    return True
