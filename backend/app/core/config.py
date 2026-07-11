from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os

# Absolute path to backend root
_BASE = Path(__file__).resolve().parent.parent.parent

_env = os.getenv("APP_ENV", "local")
_env_file = _BASE / f".env.{_env}"

# Load explicitly — silently skips if file doesn't exist (e.g. on Render)
load_dotenv(dotenv_path=_env_file, override=True)


class Settings(BaseSettings):
    # Database
    SUPABASE_DATABASE_URL: str
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # AI
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # RAG
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5

    # CORS
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()