import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AirSpace"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # Security & Authentication
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    AUTH_RATE_LIMIT: str = "10/minute"
    REFLECT_RATE_LIMIT: str = "8/minute"
    MAX_VENT_CHARS: int = 12000
    RATE_LIMIT_ENABLED: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./airspace.db"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v:
            return "sqlite:///./airspace.db"
        # Render PostgreSQL URLs start with postgres://, SQLAlchemy requires postgresql://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # AI Provider Configuration (Decompress & Reframe)
    AI_PROVIDER: str = "gemini"  # "gemini", "mock" (for tests / fallback)
    AI_PROVIDER_API_KEY: str = ""
    AI_MODEL_NAME: str = "gemini-3.8-flash"
    AI_PROMPT_VERSION: str = "v1.0"
    
    
    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://airspace.onrender.com",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
