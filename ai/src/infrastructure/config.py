"""Configuration for the AI processing module."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Resolve project paths from ai/src/infrastructure
AI_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = Path(__file__).resolve().parents[3]
root_env_path = ROOT_DIR / ".env"
ai_env_path = AI_DIR / ".env"

# Try root .env first, then fallback to ai/.env
if root_env_path.exists():
    load_dotenv(root_env_path)
elif ai_env_path.exists():
    load_dotenv(ai_env_path)

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from settings import settings as global_settings

class Config:
    """Main configuration class for the AI processing system."""

    # OpenAI Configuration (only secret from env)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", global_settings.OPENAI_API_KEY)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", global_settings.OPENAI_MODEL)
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", str(global_settings.OPENAI_MAX_TOKENS)))
    OPENAI_TEMPERATURE: float = float(
        os.getenv("OPENAI_TEMPERATURE", str(global_settings.OPENAI_TEMPERATURE))
    )

    # Data Processing Configuration
    MAX_CONCURRENT_REQUESTS: int = int(
        os.getenv("MAX_CONCURRENT_REQUESTS", str(global_settings.MAX_CONCURRENT_REQUESTS))
    )
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", str(global_settings.REQUEST_DELAY)))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", str(global_settings.CHUNK_SIZE)))

    # File Paths (with fallback to ai/ subdirectories)
    DATA_DIR: str = str(AI_DIR / global_settings.DATA_DIR_NAME)
    OUTPUT_DIR: str = str(AI_DIR / global_settings.OUTPUT_DIR_NAME)
    CACHE_DIR: str = str(AI_DIR / global_settings.CACHE_DIR_NAME)
    CSV_FILE: str = "SB_publication_PMC.csv"

    # Processing Settings
    MAX_ARTICLES_TO_PROCESS: Optional[int] = None  # Set to None for all articles
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", str(global_settings.BATCH_SIZE)))

    # OpenAI Prompts
    ORGANISM_EXTRACTION_PROMPT = """
    Analyze the following scientific article title and extract information about organisms mentioned.
    Return a JSON object with the following structure:
    {{
        "organisms": ["organism1", "organism2"],
        "organism_types": ["mammal", "plant", "bacteria", "etc"],
        "study_subjects": ["cells", "tissues", "organs", "etc"],
        "environment": "lab/production/simulation"
    }}
    
    Article Title: {title}
    """
    
    ARTICLE_SUMMARY_PROMPT = """
    Provide a comprehensive summary of this scientific article.
    Include the following sections:
    1. Research Objective
    2. Methodology
    3. Key Findings
    4. Practical and research implications
    5. Organisms Studied
    6. Environmental Conditions
    
    Article Title: {title}
    Article Content: {content}
    
    Format the response in clear, structured sections.
    """
    
    KNOWLEDGE_GRAPH_PROMPT = """
    Analyze this research article and identify key relationships and connections.
    Return a JSON object with:
    {{
        "key_concepts": ["concept1", "concept2"],
        "biological_processes": ["process1", "process2"],
        "domain_effects": ["effect1", "effect2"],
        "research_gaps": ["gap1", "gap2"],
        "connections": [
            {{"from": "concept1", "to": "concept2", "relationship": "affects"}}
        ]
    }}
    
    Article: {title}
    Content: {content}
    """

# Validate configuration
def validate_config() -> bool:
    """Validate that all required configuration is present."""
    if not Config.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable is required")
        return False
    
    if not os.path.exists(Config.DATA_DIR):
        print(f"ERROR: Data directory {Config.DATA_DIR} does not exist")
        return False
    
    return True

# Create necessary directories
def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(Config.CACHE_DIR, exist_ok=True)
