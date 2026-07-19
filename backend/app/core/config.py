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
load_dotenv(dotenv_path=_env_file, override=False)


class Settings(BaseSettings):
    APP_ENV: str = _env

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
    CORS_ORIGINS: str = "http://localhost:5173"

    # Filesystem storage. In production this must point at a persistent mount.
    UPLOAD_ROOT: str = ""
    MAX_UPLOAD_MB: int = 25

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if self.APP_ENV.lower() == "production" and "*" in origins:
            raise ValueError("Wildcard CORS is not allowed when APP_ENV=production")
        return origins

    @property
    def upload_root_path(self) -> Path:
        raw = self.UPLOAD_ROOT.strip()
        if not raw:
            if self.APP_ENV.lower() == "production":
                raise ValueError(
                    "UPLOAD_ROOT must point at persistent storage when APP_ENV=production"
                )
            return (_BASE / "uploads").resolve()
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = _BASE / path
        return path.resolve()

@lru_cache()
def get_settings() -> Settings:
    return Settings()
