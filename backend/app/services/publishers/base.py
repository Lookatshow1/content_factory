"""
Base Publisher - Abstract base class for all platform publishers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PublishResult:
    """Result of publishing a video."""
    success: bool
    platform_video_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None


class BasePublisher(ABC):
    """
    Abstract base class for platform publishers.
    Each platform implements its own publish logic.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform name."""
        pass

    @abstractmethod
    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        thumbnail_path: Optional[str] = None,
    ) -> PublishResult:
        """
        Publish video to the platform.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Optional thumbnail image

        Returns:
            PublishResult with status and platform-specific IDs
        """
        pass

    @abstractmethod
    async def is_configured(self) -> bool:
        """Check if publisher is properly configured."""
        pass

    def format_hashtags(self, hashtags: List[str], prefix: str = "#") -> str:
        """
        Format hashtags for the platform.

        Args:
            hashtags: List of hashtag strings
            prefix: Prefix to add (default "#")

        Returns:
            Formatted hashtag string
        """
        return " ".join(
            f"{prefix}{tag.lstrip('#')}" for tag in hashtags if tag
        )
