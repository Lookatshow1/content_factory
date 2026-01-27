"""
YouTube Publisher - Upload videos to YouTube Shorts.
Uses YouTube Data API v3.
"""
import os
from typing import Optional, List

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.core.config import settings
from app.services.publishers.base import BasePublisher, PublishResult


class YouTubePublisher(BasePublisher):
    """
    Publishes videos to YouTube as Shorts.
    Requires OAuth2 credentials with youtube.upload scope.
    """

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    @property
    def platform_name(self) -> str:
        return "youtube"

    async def is_configured(self) -> bool:
        """Check if YouTube API is configured."""
        return bool(
            settings.youtube_client_id
            and settings.youtube_client_secret
            and settings.youtube_refresh_token
        )

    def _get_credentials(self) -> Credentials:
        """Get OAuth2 credentials."""
        credentials = Credentials(
            token=None,
            refresh_token=settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
        )

        if credentials.expired or not credentials.valid:
            credentials.refresh(Request())

        return credentials

    async def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        hashtags: List[str],
        thumbnail_path: Optional[str] = None,
    ) -> PublishResult:
        """
        Upload video to YouTube as a Short.

        Args:
            video_path: Path to video file
            title: Video title (max 100 chars for Shorts)
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Optional custom thumbnail

        Returns:
            PublishResult with YouTube video ID and URL
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="YouTube API not configured",
            )

        try:
            credentials = self._get_credentials()
            youtube = build("youtube", "v3", credentials=credentials)

            # Format description with hashtags
            # Adding #Shorts helps YouTube identify it as a Short
            formatted_hashtags = self.format_hashtags(hashtags)
            full_description = f"{description}\n\n{formatted_hashtags}\n#Shorts"

            # Prepare video metadata
            body = {
                "snippet": {
                    "title": title[:100],  # YouTube title limit
                    "description": full_description,
                    "tags": hashtags[:500],  # YouTube tags limit
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            }

            # Upload video
            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024,  # 1MB chunks
            )

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response["id"]

            # Upload custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path),
                    ).execute()
                except Exception:
                    pass  # Thumbnail upload is not critical

            return PublishResult(
                success=True,
                platform_video_id=video_id,
                platform_url=f"https://youtube.com/shorts/{video_id}",
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )
