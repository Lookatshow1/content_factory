"""
TikTok Publisher - Upload videos to TikTok.
Uses TikTok Content Posting API.
"""
import os
import time
import asyncio
from typing import Optional, List

import httpx

from app.core.config import settings
from app.services.publishers.base import BasePublisher, PublishResult


class TikTokPublisher(BasePublisher):
    """
    Publishes videos to TikTok.
    Uses the official Content Posting API.
    """

    API_URL = "https://open.tiktokapis.com/v2"

    @property
    def platform_name(self) -> str:
        return "tiktok"

    async def is_configured(self) -> bool:
        """Check if TikTok API is configured."""
        return bool(
            settings.tiktok_client_key
            and settings.tiktok_client_secret
            and settings.tiktok_access_token
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
        Upload video to TikTok.

        Args:
            video_path: Path to video file
            title: Video title (used in description)
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Not used for TikTok

        Returns:
            PublishResult with TikTok video ID
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="TikTok API not configured",
            )

        try:
            # Step 1: Initialize upload
            video_size = os.path.getsize(video_path)
            init_response = await self._init_upload(video_size)

            if not init_response.get("data"):
                return PublishResult(
                    success=False,
                    error_message=f"Failed to init upload: {init_response}",
                )

            upload_url = init_response["data"]["upload_url"]
            publish_id = init_response["data"]["publish_id"]

            # Step 2: Upload video file
            await self._upload_video(upload_url, video_path)

            # Step 3: Publish the video
            caption = self._format_caption(title, description, hashtags)
            publish_response = await self._publish_video(publish_id, caption)

            if publish_response.get("error", {}).get("code") != "ok":
                return PublishResult(
                    success=False,
                    error_message=f"Failed to publish: {publish_response}",
                )

            # Step 4: Poll for completion
            video_id = await self._wait_for_publish(publish_id)

            return PublishResult(
                success=True,
                platform_video_id=video_id,
                platform_url=f"https://www.tiktok.com/@user/video/{video_id}",
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    async def _init_upload(self, video_size: int) -> dict:
        """Initialize video upload."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/post/publish/video/init/",
                headers={
                    "Authorization": f"Bearer {settings.tiktok_access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "post_info": {
                        "title": "",  # Title goes in caption
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_stitch": False,
                        "disable_comment": False,
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": video_size,
                        "chunk_size": video_size,
                        "total_chunk_count": 1,
                    },
                },
            )
            return response.json()

    async def _upload_video(self, upload_url: str, video_path: str):
        """Upload video file to TikTok."""
        video_size = os.path.getsize(video_path)

        async with httpx.AsyncClient() as client:
            with open(video_path, "rb") as f:
                response = await client.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(video_size),
                        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
                    },
                    content=f.read(),
                    timeout=300,
                )
                response.raise_for_status()

    async def _publish_video(self, publish_id: str, caption: str) -> dict:
        """Complete the publishing process."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/post/publish/status/fetch/",
                headers={
                    "Authorization": f"Bearer {settings.tiktok_access_token}",
                    "Content-Type": "application/json",
                },
                json={"publish_id": publish_id},
            )
            return response.json()

    async def _wait_for_publish(
        self,
        publish_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> str:
        """Poll until video is published."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                response = await client.post(
                    f"{self.API_URL}/post/publish/status/fetch/",
                    headers={
                        "Authorization": f"Bearer {settings.tiktok_access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"publish_id": publish_id},
                )
                data = response.json()

                status = data.get("data", {}).get("status")
                if status == "PUBLISH_COMPLETE":
                    return data["data"].get("video_id", publish_id)
                elif status in ["FAILED", "REJECTED"]:
                    raise Exception(f"TikTok publish failed: {data}")

                await asyncio.sleep(poll_interval)

        raise TimeoutError("TikTok publish timed out")

    def _format_caption(
        self,
        title: str,
        description: str,
        hashtags: List[str],
    ) -> str:
        """Format caption for TikTok."""
        formatted_hashtags = self.format_hashtags(hashtags)
        # TikTok caption limit is 2200 characters
        caption = f"{title}\n\n{description}\n\n{formatted_hashtags}"
        return caption[:2200]
