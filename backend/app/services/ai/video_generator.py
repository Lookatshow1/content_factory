"""
Video Generator using HeyGen and FAL.ai (Kling) APIs.
Generates AI avatar videos and AI-generated video content.
"""
import os
import time
import uuid
import asyncio
from typing import Optional
from pathlib import Path
from enum import Enum

import httpx
import aiohttp

from app.core.config import settings


class VideoType(str, Enum):
    AVATAR = "avatar"  # HeyGen talking head
    AI_GENERATED = "ai_generated"  # Kling/Runway AI video


class VideoGenerator:
    """
    Generates videos using AI services.
    - HeyGen for avatar/talking head videos
    - FAL.ai (Kling) for AI-generated video content
    """

    HEYGEN_API_URL = "https://api.heygen.com"
    FAL_API_URL = "https://queue.fal.run"

    def __init__(self):
        self.heygen_key = settings.heygen_api_key
        self.fal_key = settings.fal_api_key

    def _get_proxy_config(self) -> dict:
        """Get proxy configuration for httpx."""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        return proxies if proxies else None

    def _get_aiohttp_proxy(self) -> Optional[str]:
        """Get proxy URL for aiohttp."""
        return settings.https_proxy or settings.http_proxy

    # =========================================================================
    # HeyGen Avatar Videos
    # =========================================================================

    async def generate_avatar_video(
        self,
        script: str,
        audio_path: Optional[str] = None,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        aspect_ratio: str = "9:16",  # Vertical for shorts
    ) -> str:
        """
        Generate a talking avatar video using HeyGen.

        Args:
            script: Text for the avatar to speak
            audio_path: Pre-generated audio file (optional)
            avatar_id: HeyGen avatar ID
            voice_id: HeyGen voice ID (if not using audio_path)
            output_path: Where to save the video
            aspect_ratio: Video aspect ratio

        Returns:
            Path to generated video
        """
        if not self.heygen_key:
            raise ValueError("HEYGEN_API_KEY not configured")

        # Default avatar
        avatar_id = avatar_id or "Angela-inblackskirt-20220820"

        # Prepare request
        if audio_path:
            # Upload audio and create video
            video_id = await self._heygen_create_video_with_audio(
                script=script,
                audio_path=audio_path,
                avatar_id=avatar_id,
                aspect_ratio=aspect_ratio,
            )
        else:
            # Use HeyGen's TTS
            video_id = await self._heygen_create_video(
                script=script,
                avatar_id=avatar_id,
                voice_id=voice_id or "en-US-JennyNeural",
                aspect_ratio=aspect_ratio,
            )

        # Poll for completion
        video_url = await self._heygen_wait_for_video(video_id)

        # Download video
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await self._download_file(video_url, output_path)

        return output_path

    async def _heygen_create_video(
        self,
        script: str,
        avatar_id: str,
        voice_id: str,
        aspect_ratio: str,
    ) -> str:
        """Create video using HeyGen's TTS."""
        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.post(
                f"{self.HEYGEN_API_URL}/v2/video/generate",
                headers={
                    "X-Api-Key": self.heygen_key,
                    "Content-Type": "application/json",
                },
                json={
                    "video_inputs": [
                        {
                            "character": {
                                "type": "avatar",
                                "avatar_id": avatar_id,
                                "avatar_style": "normal",
                            },
                            "voice": {
                                "type": "text",
                                "input_text": script,
                                "voice_id": voice_id,
                            },
                        }
                    ],
                    "dimension": self._get_dimension(aspect_ratio),
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["video_id"]

    async def _heygen_create_video_with_audio(
        self,
        script: str,
        audio_path: str,
        avatar_id: str,
        aspect_ratio: str,
    ) -> str:
        """Create video using pre-generated audio."""
        # First, upload the audio file
        audio_url = await self._heygen_upload_audio(audio_path)

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.post(
                f"{self.HEYGEN_API_URL}/v2/video/generate",
                headers={
                    "X-Api-Key": self.heygen_key,
                    "Content-Type": "application/json",
                },
                json={
                    "video_inputs": [
                        {
                            "character": {
                                "type": "avatar",
                                "avatar_id": avatar_id,
                                "avatar_style": "normal",
                            },
                            "voice": {
                                "type": "audio",
                                "audio_url": audio_url,
                            },
                        }
                    ],
                    "dimension": self._get_dimension(aspect_ratio),
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["video_id"]

    async def _heygen_upload_audio(self, audio_path: str) -> str:
        """Upload audio file to HeyGen."""
        proxy = self._get_aiohttp_proxy()
        connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(connector=connector) as session:
            with open(audio_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    f,
                    filename=os.path.basename(audio_path),
                    content_type="audio/mpeg",
                )

                async with session.post(
                    f"{self.HEYGEN_API_URL}/v1/asset",
                    headers={"X-Api-Key": self.heygen_key},
                    data=data,
                    proxy=proxy,
                ) as response:
                    result = await response.json()
                    return result["data"]["url"]

    async def _heygen_wait_for_video(
        self,
        video_id: str,
        timeout: int = 600,
        poll_interval: int = 10,
    ) -> str:
        """Poll HeyGen until video is ready."""
        start_time = time.time()

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            while time.time() - start_time < timeout:
                response = await client.get(
                    f"{self.HEYGEN_API_URL}/v1/video_status.get",
                    headers={"X-Api-Key": self.heygen_key},
                    params={"video_id": video_id},
                )
                response.raise_for_status()
                data = response.json()

                status = data["data"]["status"]
                if status == "completed":
                    return data["data"]["video_url"]
                elif status == "failed":
                    raise Exception(f"HeyGen video generation failed: {data}")

                await asyncio.sleep(poll_interval)

        raise TimeoutError("HeyGen video generation timed out")

    # =========================================================================
    # FAL.ai / Kling AI Videos
    # =========================================================================

    async def generate_ai_video(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "9:16",
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate AI video using Kling via FAL.ai.

        Args:
            prompt: Text description of the video
            duration: Video duration in seconds (5-10)
            aspect_ratio: Video aspect ratio
            output_path: Where to save the video

        Returns:
            Path to generated video
        """
        if not self.fal_key:
            raise ValueError("FAL_API_KEY not configured")

        # Submit generation request
        request_id = await self._fal_submit_video(prompt, duration, aspect_ratio)

        # Poll for completion
        video_url = await self._fal_wait_for_video(request_id)

        # Download video
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await self._download_file(video_url, output_path)

        return output_path

    async def _fal_submit_video(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
    ) -> str:
        """Submit video generation request to FAL.ai."""
        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.post(
                f"{self.FAL_API_URL}/fal-ai/kling-video/v1.6/pro/text-to-video",
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "duration": str(duration),
                    "aspect_ratio": aspect_ratio,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["request_id"]

    async def _fal_wait_for_video(
        self,
        request_id: str,
        timeout: int = 600,
        poll_interval: int = 10,
    ) -> str:
        """Poll FAL.ai until video is ready."""
        start_time = time.time()

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            while time.time() - start_time < timeout:
                response = await client.get(
                    f"{self.FAL_API_URL}/fal-ai/kling-video/requests/{request_id}/status",
                    headers={"Authorization": f"Key {self.fal_key}"},
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                if status == "COMPLETED":
                    # Get result
                    result_response = await client.get(
                        f"{self.FAL_API_URL}/fal-ai/kling-video/requests/{request_id}",
                        headers={"Authorization": f"Key {self.fal_key}"},
                    )
                    result_response.raise_for_status()
                    result = result_response.json()
                    return result["video"]["url"]
                elif status == "FAILED":
                    raise Exception(f"FAL video generation failed: {data}")

                await asyncio.sleep(poll_interval)

        raise TimeoutError("FAL video generation timed out")

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_dimension(self, aspect_ratio: str) -> dict:
        """Convert aspect ratio to dimensions."""
        dimensions = {
            "9:16": {"width": 1080, "height": 1920},  # Vertical
            "16:9": {"width": 1920, "height": 1080},  # Horizontal
            "1:1": {"width": 1080, "height": 1080},   # Square
        }
        return dimensions.get(aspect_ratio, dimensions["9:16"])

    async def _download_file(self, url: str, output_path: str):
        """Download a file from URL."""
        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.get(url, timeout=120)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)

    async def get_heygen_avatars(self) -> list[dict]:
        """Get list of available HeyGen avatars."""
        if not self.heygen_key:
            return []

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.get(
                f"{self.HEYGEN_API_URL}/v2/avatars",
                headers={"X-Api-Key": self.heygen_key},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("avatars", [])
