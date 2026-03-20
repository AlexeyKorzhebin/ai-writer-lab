from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./writer.db"

    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-3.5-turbo"
    llm_timeout: float = 120.0

    max_orchestrator_iterations: int = 3
    orchestrator_min_score: int = 8

    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
