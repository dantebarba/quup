"""Configuration management using Pydantic Settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Security
    api_auth_token: str = Field(..., description="API authentication token")
    
    # Plex Configuration
    plex_url: str = Field(..., description="Plex server URL")
    plex_token: str = Field(..., description="Plex authentication token")
    plex_library_name: str = Field(default="Pelis", description="Plex library name")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")
    openai_assistant_name: str = Field(
        default="Plex AI Curator",
        description="Name for the OpenAI assistant"
    )
    
    # Feature Toggles
    enable_telegram: bool = Field(default=False, description="Enable Telegram notifications")
    enable_plex_playlist: bool = Field(default=True, description="Enable Plex playlist creation")
    
    # Telegram Configuration
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID")
    
    # Application Settings
    recommendation_count: int = Field(default=10, description="Number of movies to recommend")
    history_lookback: int = Field(default=5, description="Number of recent movies to analyze")
    playlist_name: str = Field(
        default="Recomendado por IA",
        description="Name for the Plex playlist"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Global settings instance
settings = Settings()
