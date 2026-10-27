from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IntelliChurn API"
    database_url: str = "sqlite:///./intellchurn.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    model_path: str = "ml_pipeline/saved_models/churn_bundle.joblib"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
