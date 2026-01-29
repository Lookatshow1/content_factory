"""
Stock Footage Service - integration with Pexels, Pixabay, and other stock sources.
"""
import os
import uuid
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass
class StockMedia:
    """Represents a stock media item."""
    id: str
    source: str  # pexels, pixabay
    type: str  # video, image
    url: str
    preview_url: str
    download_url: str
    width: int
    height: int
    duration: Optional[float] = None  # For videos
    author: Optional[str] = None


class StockFootageService:
    """
    Fetches stock videos and images from Pexels and Pixabay.
    Both have free APIs with attribution requirements.
    """

    PEXELS_API_URL = "https://api.pexels.com"
    PIXABAY_API_URL = "https://pixabay.com/api"

    def __init__(self):
        self.pexels_key = settings.pexels_api_key if hasattr(settings, 'pexels_api_key') else None
        self.pixabay_key = settings.pixabay_api_key if hasattr(settings, 'pixabay_api_key') else None

    def _get_proxy_config(self) -> dict:
        """Get proxy configuration for httpx."""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        return proxies if proxies else None

    async def search_videos(
        self,
        query: str,
        orientation: str = "portrait",  # portrait, landscape, square
        per_page: int = 10,
        source: str = "pexels",  # pexels or pixabay
    ) -> list[StockMedia]:
        """
        Search for stock videos.

        Args:
            query: Search query
            orientation: Video orientation
            per_page: Number of results
            source: Stock source to use

        Returns:
            List of StockMedia items
        """
        if source == "pexels" and self.pexels_key:
            return await self._search_pexels_videos(query, orientation, per_page)
        elif source == "pixabay" and self.pixabay_key:
            return await self._search_pixabay_videos(query, orientation, per_page)
        else:
            # Try both sources
            results = []
            if self.pexels_key:
                results.extend(await self._search_pexels_videos(query, orientation, per_page // 2))
            if self.pixabay_key:
                results.extend(await self._search_pixabay_videos(query, orientation, per_page // 2))
            return results

    async def search_images(
        self,
        query: str,
        orientation: str = "vertical",
        per_page: int = 10,
        source: str = "pexels",
    ) -> list[StockMedia]:
        """
        Search for stock images.

        Args:
            query: Search query
            orientation: Image orientation
            per_page: Number of results
            source: Stock source to use

        Returns:
            List of StockMedia items
        """
        if source == "pexels" and self.pexels_key:
            return await self._search_pexels_images(query, orientation, per_page)
        elif source == "pixabay" and self.pixabay_key:
            return await self._search_pixabay_images(query, orientation, per_page)
        else:
            results = []
            if self.pexels_key:
                results.extend(await self._search_pexels_images(query, orientation, per_page // 2))
            if self.pixabay_key:
                results.extend(await self._search_pixabay_images(query, orientation, per_page // 2))
            return results

    async def download_media(
        self,
        media: StockMedia,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Download a stock media item.

        Args:
            media: StockMedia item to download
            output_path: Where to save the file

        Returns:
            Path to downloaded file
        """
        if output_path is None:
            ext = "mp4" if media.type == "video" else "jpg"
            filename = f"{media.source}_{media.id}.{ext}"
            subdir = "stock_videos" if media.type == "video" else "stock_images"
            output_path = os.path.join(settings.media_dir, subdir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=120.0, proxy=proxy_config) as client:
            response = await client.get(media.download_url)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)

        return output_path

    # =========================================================================
    # Pexels API
    # =========================================================================

    async def _search_pexels_videos(
        self,
        query: str,
        orientation: str,
        per_page: int,
    ) -> list[StockMedia]:
        """Search Pexels for videos."""
        if not self.pexels_key:
            return []

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=30.0, proxy=proxy_config) as client:
            response = await client.get(
                f"{self.PEXELS_API_URL}/videos/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": per_page,
                    "size": "medium",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for video in data.get("videos", []):
            # Get the best quality video file
            video_files = video.get("video_files", [])
            best_file = max(video_files, key=lambda x: x.get("width", 0), default=None)

            if best_file:
                results.append(StockMedia(
                    id=str(video["id"]),
                    source="pexels",
                    type="video",
                    url=video.get("url", ""),
                    preview_url=video.get("image", ""),
                    download_url=best_file["link"],
                    width=best_file.get("width", 1920),
                    height=best_file.get("height", 1080),
                    duration=video.get("duration"),
                    author=video.get("user", {}).get("name"),
                ))

        return results

    async def _search_pexels_images(
        self,
        query: str,
        orientation: str,
        per_page: int,
    ) -> list[StockMedia]:
        """Search Pexels for images."""
        if not self.pexels_key:
            return []

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=30.0, proxy=proxy_config) as client:
            response = await client.get(
                f"{self.PEXELS_API_URL}/v1/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": per_page,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for photo in data.get("photos", []):
            results.append(StockMedia(
                id=str(photo["id"]),
                source="pexels",
                type="image",
                url=photo.get("url", ""),
                preview_url=photo.get("src", {}).get("medium", ""),
                download_url=photo.get("src", {}).get("large2x", photo.get("src", {}).get("original", "")),
                width=photo.get("width", 1920),
                height=photo.get("height", 1080),
                author=photo.get("photographer"),
            ))

        return results

    # =========================================================================
    # Pixabay API
    # =========================================================================

    async def _search_pixabay_videos(
        self,
        query: str,
        orientation: str,
        per_page: int,
    ) -> list[StockMedia]:
        """Search Pixabay for videos."""
        if not self.pixabay_key:
            return []

        # Map orientation
        pixabay_orientation = {
            "portrait": "vertical",
            "landscape": "horizontal",
            "square": "all",
        }.get(orientation, "all")

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=30.0, proxy=proxy_config) as client:
            response = await client.get(
                f"{self.PIXABAY_API_URL}/videos/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "orientation": pixabay_orientation,
                    "per_page": per_page,
                    "safesearch": "true",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for video in data.get("hits", []):
            videos = video.get("videos", {})
            # Prefer large, then medium
            best = videos.get("large", videos.get("medium", {}))

            if best:
                results.append(StockMedia(
                    id=str(video["id"]),
                    source="pixabay",
                    type="video",
                    url=video.get("pageURL", ""),
                    preview_url=f"https://i.vimeocdn.com/video/{video.get('picture_id')}_640x360.jpg",
                    download_url=best.get("url", ""),
                    width=best.get("width", 1920),
                    height=best.get("height", 1080),
                    duration=video.get("duration"),
                    author=video.get("user"),
                ))

        return results

    async def _search_pixabay_images(
        self,
        query: str,
        orientation: str,
        per_page: int,
    ) -> list[StockMedia]:
        """Search Pixabay for images."""
        if not self.pixabay_key:
            return []

        pixabay_orientation = {
            "vertical": "vertical",
            "portrait": "vertical",
            "landscape": "horizontal",
            "horizontal": "horizontal",
        }.get(orientation, "all")

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=30.0, proxy=proxy_config) as client:
            response = await client.get(
                f"{self.PIXABAY_API_URL}/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "orientation": pixabay_orientation,
                    "per_page": per_page,
                    "safesearch": "true",
                    "image_type": "photo",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for image in data.get("hits", []):
            results.append(StockMedia(
                id=str(image["id"]),
                source="pixabay",
                type="image",
                url=image.get("pageURL", ""),
                preview_url=image.get("webformatURL", ""),
                download_url=image.get("largeImageURL", ""),
                width=image.get("imageWidth", 1920),
                height=image.get("imageHeight", 1080),
                author=image.get("user"),
            ))

        return results

    def is_configured(self) -> bool:
        """Check if any stock source is configured."""
        return bool(self.pexels_key or self.pixabay_key)
