"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://content_factory:changeme@localhost:5432/content_factory"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI Services
    anthropic_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    heygen_api_key: Optional[str] = None
    fal_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Publishing - YouTube
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    youtube_refresh_token: Optional[str] = None

    # Publishing - TikTok
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    tiktok_access_token: Optional[str] = None

    # Publishing - VK
    vk_access_token: Optional[str] = None
    vk_group_id: Optional[str] = None

    # Publishing - Telegram
    telegram_bot_token: Optional[str] = None
    telegram_channel_id: Optional[str] = None

    # Publishing - Instagram
    instagram_access_token: Optional[str] = None
    instagram_account_id: Optional[str] = None

    # Application Settings
    videos_per_week: int = 5
    default_video_duration: int = 45
    default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs Rachel voice

    # Media paths
    media_dir: str = "media"

    @property
    def video_dir(self) -> str:
        return f"{self.media_dir}/videos"

    @property
    def audio_dir(self) -> str:
        return f"{self.media_dir}/audio"

    @property
    def thumbnail_dir(self) -> str:
        return f"{self.media_dir}/thumbnails"

    @property
    def temp_dir(self) -> str:
        return f"{self.media_dir}/temp"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
