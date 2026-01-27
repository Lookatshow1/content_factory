"""
VK Publisher - Upload videos to VK Clips.
Uses VK API.
"""
import os
from typing import Optional, List

import vk_api

from app.core.config import settings
from app.services.publishers.base import BasePublisher, PublishResult


class VKPublisher(BasePublisher):
    """
    Publishes videos to VK as Clips.
    Uses vk-api library for API interaction.
    """

    @property
    def platform_name(self) -> str:
        return "vk"

    async def is_configured(self) -> bool:
        """Check if VK API is configured."""
        return bool(settings.vk_access_token)

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        thumbnail_path: Optional[str] = None,
    ) -> PublishResult:
        """
        Upload video to VK as a Clip.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Not used

        Returns:
            PublishResult with VK video ID and URL
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="VK API not configured",
            )

        try:
            # Initialize VK API session
            vk_session = vk_api.VkApi(token=settings.vk_access_token)
            vk = vk_session.get_api()
            upload = vk_api.VkUpload(vk_session)

            # Format description with hashtags
            formatted_hashtags = self.format_hashtags(hashtags)
            full_description = f"{description}\n\n{formatted_hashtags}"

            # Determine group_id if posting to group
            group_id = None
            if settings.vk_group_id:
                group_id = int(settings.vk_group_id.lstrip("-"))

            # Upload video
            # For Clips, we use is_private=0 and wallpost=0
            video_info = upload.video(
                video_file=video_path,
                name=title[:128],  # VK title limit
                description=full_description[:5000],  # VK description limit
                group_id=group_id,
                is_private=False,
                wallpost=False,  # Don't post to wall, just upload
            )

            video_id = video_info.get("video_id")
            owner_id = video_info.get("owner_id")

            if not video_id:
                return PublishResult(
                    success=False,
                    error_message=f"Failed to upload: {video_info}",
                )

            # For clips, we might need to post separately
            # VK Clips are essentially short videos posted in a special section

            return PublishResult(
                success=True,
                platform_video_id=str(video_id),
                platform_url=f"https://vk.com/video{owner_id}_{video_id}",
            )

        except vk_api.VkApiError as e:
            return PublishResult(
                success=False,
                error_message=f"VK API error: {e}",
            )
        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    async def post_to_wall(
        self,
        video_id: str,
        owner_id: str,
        message: str,
    ) -> bool:
        """
        Post video to wall (optional, for additional reach).

        Args:
            video_id: VK video ID
            owner_id: Video owner ID
            message: Post message

        Returns:
            True if successful
        """
        try:
            vk_session = vk_api.VkApi(token=settings.vk_access_token)
            vk = vk_session.get_api()

            vk.wall.post(
                owner_id=owner_id if not settings.vk_group_id else f"-{settings.vk_group_id}",
                message=message,
                attachments=f"video{owner_id}_{video_id}",
            )
            return True
        except Exception:
            return False
