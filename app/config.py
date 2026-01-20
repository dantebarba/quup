from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security
    API_AUTH_TOKEN: str = Field(..., description="Token for x-api-token header validation")

    # Plex
    PLEX_URL: Optional[str] = Field(None, description="Plex server URL")
    PLEX_TOKEN: Optional[str] = Field(None, description="Plex token")
    PLEX_LIBRARY_NAME: Optional[str] = Field(None, description="Plex library name")

    # OpenAI / Assistants
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    OPENAI_MODEL: str = Field("gpt-4o", description="Default OpenAI model")
    OPENAI_ASSISTANT_NAME: Optional[str] = Field(None, description="Assistant name")

    # Features
    ENABLE_TELEGRAM: bool = Field(False, description="Enable Telegram notifications")
    ENABLE_PLEX_PLAYLIST: bool = Field(False, description="Enable Plex playlist updates")

    # Notifications (Telegram)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

