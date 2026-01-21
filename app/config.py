# app/config.py
from __future__ import annotations
import os
from typing import Optional


class Settings:
    def __init__(
        self,
        api_token: str,
        plex_url: str,
        plex_token: str,
        library_name: str,
        openai_key: str,
        model: str,
        assistant_name: str,
        enable_telegram: bool,
        enable_plex_playlist: bool,
        telegram_bot_token: Optional[str],
        telegram_chat_id: Optional[str],
    ):
        self.api_token = api_token
        self.plex_url = plex_url
        self.plex_token = plex_token
        self.library_name = library_name
        self.openai_key = openai_key
        self.model = model
        self.assistant_name = assistant_name
        self.enable_telegram = enable_telegram
        self.enable_plex_playlist = enable_plex_playlist
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id


def _load_settings() -> Settings:
    return Settings(
        api_token=os.getenv("API_AUTH_TOKEN", "default-token"),
        plex_url=os.getenv("PLEX_URL", ""),
        plex_token=os.getenv("PLEX_TOKEN", ""),
        library_name=os.getenv("PLEX_LIBRARY", "Main"),
        openai_key=os.getenv("OPENAI_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        assistant_name=os.getenv("ASSISTANT_NAME", "PlexAI"),
        enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower()
        in ("true", "1", "yes", "y"),
        enable_plex_playlist=os.getenv("ENABLE_PLEX_PLAYLIST", "true").lower()
        in ("true", "1", "yes", "y"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    )


_settings = _load_settings()


def get_settings() -> Settings:
    return _settings
