import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application Settings
    Zero-hardcoding configuration loaded from environment variables and .env file.
    """
    # Project Identity
    PROJECT_NAME: str = "Multi-Agent AI Research & Decision System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Origins (Comma-separated in .env or list)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./multi_agent.db"
    
    # AI Provider API Keys & Settings
    DEFAULT_PROVIDER: str = "auto"  # 'auto', 'openai', 'gemini', or 'mock'
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Web Search Configuration
    SEARCH_MAX_RESULTS: int = 5
    ENABLE_LIVE_SEARCH: bool = True
    
    # Human-In-The-Loop (HITL) Behavior
    REQUIRE_HUMAN_APPROVAL: bool = True
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()
