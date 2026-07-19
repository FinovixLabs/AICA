import pytest

from app.core.config import Settings


def _settings(**overrides):
    return Settings(
        SUPABASE_DATABASE_URL="postgresql://example.invalid/database",
        **overrides,
    )


def test_production_rejects_wildcard_cors():
    settings = _settings(APP_ENV="production", CORS_ORIGINS="*")
    with pytest.raises(ValueError, match="Wildcard CORS"):
        _ = settings.cors_origins_list


def test_production_requires_explicit_upload_root():
    settings = _settings(APP_ENV="production", UPLOAD_ROOT="")
    with pytest.raises(ValueError, match="UPLOAD_ROOT"):
        _ = settings.upload_root_path


def test_local_upload_root_remains_available():
    settings = _settings(APP_ENV="local", UPLOAD_ROOT="")
    assert settings.upload_root_path.name == "uploads"
