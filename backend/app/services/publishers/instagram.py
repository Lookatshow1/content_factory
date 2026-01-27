"""
Instagram Publisher - Upload videos to Instagram Reels.
Uses Instagram Graph API (via Facebook Business).
"""
import time
import asyncio
from typing import Optional, List

import httpx

from app.core.config import settings
from app.services.publishers.base import BasePublisher, PublishResult


class InstagramPublisher(BasePublisher):
    """
    Publishes videos to Instagram as Reels.
    Uses the Instagram Graph API via Facebook Business.

    Requirements:
    - Facebook Business account connected to Instagram
    - Instagram Professional account (Creator or Business)
    - Valid access token with required permissions
    """

    GRAPH_API_URL = "https://graph.facebook.com/v18.0"

    @property
    def platform_name(self) -> str:
        return "instagram"

    async def is_configured(self) -> bool:
        """Check if Instagram API is configured."""
        return bool(
            settings.instagram_access_token and settings.instagram_account_id
        )

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        thumbnail_path: Optional[str] = None,
    ) -> PublishResult:
        """
        Upload video to Instagram as a Reel.

        Note: Instagram requires video to be accessible via URL,
        so we need to upload it to a public location first.

        Args:
            video_path: Path to video file
            title: Video title (included in caption)
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Optional cover image

        Returns:
            PublishResult with Instagram media ID
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="Instagram API not configured",
            )

        try:
            # Format caption
            formatted_hashtags = self.format_hashtags(hashtags)
            caption = f"{title}\n\n{description}\n\n{formatted_hashtags}"
            # Instagram caption limit is 2200 characters
            caption = caption[:2200]

            # For Instagram, we need the video to be accessible via URL
            # In production, you'd upload to your CDN or use Facebook's upload API
            # For now, we'll assume video_path is actually a URL
            # or we need to upload to a temporary hosting

            # If video_path is a local file, we need to use container approach
            # Step 1: Create media container
            container_id = await self._create_reel_container(
                video_url=video_path,  # This should be a public URL
                caption=caption,
                thumbnail_url=thumbnail_path,
            )

            if not container_id:
                return PublishResult(
                    success=False,
                    error_message="Failed to create media container",
                )

            # Step 2: Wait for processing
            await self._wait_for_container(container_id)

            # Step 3: Publish the container
            media_id = await self._publish_container(container_id)

            if not media_id:
                return PublishResult(
                    success=False,
                    error_message="Failed to publish container",
                )

            return PublishResult(
                success=True,
                platform_video_id=media_id,
                platform_url=f"https://www.instagram.com/reel/{media_id}/",
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    async def _create_reel_container(
        self,
        video_url: str,
        caption: str,
        thumbnail_url: Optional[str] = None,
    ) -> Optional[str]:
        """Create a reel container for upload."""
        async with httpx.AsyncClient() as client:
            params = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": settings.instagram_access_token,
            }

            if thumbnail_url:
                params["cover_url"] = thumbnail_url

            response = await client.post(
                f"{self.GRAPH_API_URL}/{settings.instagram_account_id}/media",
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("id")

            return None

    async def _wait_for_container(
        self,
        container_id: str,
        timeout: int = 300,
        poll_interval: int = 10,
    ):
        """Wait for media container to finish processing."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                response = await client.get(
                    f"{self.GRAPH_API_URL}/{container_id}",
                    params={
                        "fields": "status_code,status",
                        "access_token": settings.instagram_access_token,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status_code")

                    if status == "FINISHED":
                        return
                    elif status == "ERROR":
                        raise Exception(f"Container processing failed: {data}")

                await asyncio.sleep(poll_interval)

        raise TimeoutError("Container processing timed out")

    async def _publish_container(self, container_id: str) -> Optional[str]:
        """Publish the processed container."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GRAPH_API_URL}/{settings.instagram_account_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": settings.instagram_access_token,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("id")

            return None

    async def get_video_url_for_upload(self, video_path: str) -> str:
        """
        Get a public URL for the video.
        In production, this would upload to your CDN.

        Args:
            video_path: Local path to video

        Returns:
            Public URL
        """
        # TODO: Implement video upload to CDN
        # Options:
        # 1. Upload to S3/GCS/Azure Blob and return presigned URL
        # 2. Upload to your own server
        # 3. Use Facebook's resumable upload API

        raise NotImplementedError(
            "Video hosting required for Instagram. "
            "Implement CDN upload or use Facebook resumable upload."
        )
