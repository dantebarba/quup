from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Security
    api_auth_token: str = Field(..., alias="API_AUTH_TOKEN")

    # Plex
    plex_url: str = Field(..., alias="PLEX_URL")
    plex_token: str = Field(..., alias="PLEX_TOKEN")
    plex_library_name: str = Field(..., alias="PLEX_LIBRARY_NAME")

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")
    openai_assistant_name: str = Field(..., alias="OPENAI_ASSISTANT_NAME")

    # Features
    enable_telegram: bool = Field(False, alias="ENABLE_TELEGRAM")
    enable_plex_playlist: bool = Field(True, alias="ENABLE_PLEX_PLAYLIST")

    # Notification Config
    telegram_bot_token: str | None = Field(None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(None, alias="TELEGRAM_CHAT_ID")

    class Config:
        env_file = ".env"

settings = Settings()
