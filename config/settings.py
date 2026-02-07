"""Application settings loaded from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic BaseSettings for env-based config. No secrets in code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_api_base: str | None = None
    vector_store_path: str = "./data/chroma"
    log_level: str = "INFO"


settings = Settings()
