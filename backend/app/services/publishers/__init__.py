"""Publishing services for different platforms."""
from app.services.publishers.youtube import YouTubePublisher
from app.services.publishers.tiktok import TikTokPublisher
from app.services.publishers.vk import VKPublisher
from app.services.publishers.telegram import TelegramPublisher
from app.services.publishers.instagram import InstagramPublisher
from app.services.publishers.base import BasePublisher, PublishResult

__all__ = [
    "YouTubePublisher",
    "TikTokPublisher",
    "VKPublisher",
    "TelegramPublisher",
    "InstagramPublisher",
    "BasePublisher",
    "PublishResult",
]
