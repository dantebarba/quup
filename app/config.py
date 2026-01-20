"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Runtime configuration driven by environment variables."""

	api_auth_token: str = Field(...)

	plex_url: Optional[AnyUrl] = Field(None)
	plex_token: Optional[str] = Field(None)
	plex_library_name: str = Field("Movies")

	openai_api_key: Optional[str] = Field(None)
	openai_model: str = Field("gpt-4o")
	openai_assistant_name: str = Field("Plex AI Curator")

	enable_telegram: bool = Field(False)
	enable_plex_playlist: bool = Field(False)

	telegram_bot_token: Optional[str] = Field(None)
	telegram_chat_id: Optional[str] = Field(None)

	use_sample_data: bool = Field(False)
	sample_data_path: Path = Field(Path("samples/movies_library.json"))

	model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

	@property
	def has_openai(self) -> bool:
		return bool(self.openai_api_key)

	@property
	def has_telegram(self) -> bool:
		return self.enable_telegram and bool(self.telegram_bot_token and self.telegram_chat_id)

	@property
	def should_use_sample(self) -> bool:
		# Prefer sample data when explicitly requested or when Plex credentials are missing.
		return self.use_sample_data or not (self.plex_url and self.plex_token)


def get_settings() -> Settings:
	return Settings()
