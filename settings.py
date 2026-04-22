"""Central project settings.

Edit this file to change default runtime parameters (model, temperature, limits, etc.).
Only sensitive secrets (like OPENAI_API_KEY) should stay in .env.
"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    # Sensitive
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Core model/runtime knobs (safe defaults, easy to tune)
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.1

    # Throughput/latency knobs
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY: float = 1.0
    CHUNK_SIZE: int = 1000
    BATCH_SIZE: int = 10
    RATE_LIMIT_PER_MINUTE: int = 60

    # Backend API defaults
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Research Assistant API"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Paths
    DATA_DIR_NAME: str = "data"
    OUTPUT_DIR_NAME: str = "output"
    CACHE_DIR_NAME: str = "cache"

    # Data API defaults
    DATA_API_DEFAULT_ARXIV_LIMIT: int = 15
    DATA_API_DEFAULT_SCHOLAR_LIMIT: int = 10
    DATA_API_MAX_IMAGES: int = 12
    DATA_API_MAX_ARTICLE_URLS: int = 5


settings = Settings()
