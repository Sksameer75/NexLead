"""Application settings and environment configuration."""

from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PRIVATE_ENV = Path.home() / ".nexlead.env"


class Settings(BaseSettings):
    """Central configuration managed via environment variables."""

    model_config = SettingsConfigDict(
        env_file=(
            BACKEND_DIR / ".env",
            BACKEND_DIR.parent / ".env",
            PRIVATE_ENV,
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "NexLead API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    DATABASE_URL: str = (
        "mysql+pymysql://root:password@127.0.0.1:3306/lead_intelligence"
    )

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []


settings = Settings()
