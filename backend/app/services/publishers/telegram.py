"""
Telegram Publisher - Post videos to Telegram channel.
Uses Telegram Bot API.
"""
import os
from typing import Optional, List

from telegram import Bot
from telegram.constants import ParseMode

from app.core.config import settings
from app.services.publishers.base import BasePublisher, PublishResult


class TelegramPublisher(BasePublisher):
    """
    Publishes videos to Telegram channel.
    Can post as regular video or as video note (for stories-like circular videos).
    """

    @property
    def platform_name(self) -> str:
        return "telegram"

    async def is_configured(self) -> bool:
        """Check if Telegram is configured."""
        return bool(
            settings.telegram_bot_token and settings.telegram_channel_id
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
        Post video to Telegram channel.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            hashtags: List of hashtags
            thumbnail_path: Optional thumbnail for video

        Returns:
            PublishResult with Telegram message ID and URL
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="Telegram not configured",
            )

        try:
            bot = Bot(token=settings.telegram_bot_token)

            # Format caption
            formatted_hashtags = self.format_hashtags(hashtags)
            caption = f"**{title}**\n\n{description}\n\n{formatted_hashtags}"
            # Telegram caption limit is 1024 characters
            caption = caption[:1024]

            # Open video file
            with open(video_path, "rb") as video_file:
                # Prepare thumbnail if available
                thumb = None
                if thumbnail_path and os.path.exists(thumbnail_path):
                    thumb = open(thumbnail_path, "rb")

                try:
                    # Send video
                    message = await bot.send_video(
                        chat_id=settings.telegram_channel_id,
                        video=video_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        thumbnail=thumb,
                        supports_streaming=True,
                    )
                finally:
                    if thumb:
                        thumb.close()

            # Construct message URL
            channel_id = settings.telegram_channel_id
            if channel_id.startswith("@"):
                channel_name = channel_id[1:]
                message_url = f"https://t.me/{channel_name}/{message.message_id}"
            elif channel_id.startswith("-100"):
                # Private channel - need to construct differently
                message_url = f"https://t.me/c/{channel_id[4:]}/{message.message_id}"
            else:
                message_url = None

            return PublishResult(
                success=True,
                platform_video_id=str(message.message_id),
                platform_url=message_url,
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    async def post_to_story(
        self,
        video_path: str,
    ) -> PublishResult:
        """
        Post video as a Telegram story (video note).
        Note: Stories require specific permissions and format.

        Args:
            video_path: Path to video file (should be square/circular format)

        Returns:
            PublishResult
        """
        if not await self.is_configured():
            return PublishResult(
                success=False,
                error_message="Telegram not configured",
            )

        try:
            bot = Bot(token=settings.telegram_bot_token)

            with open(video_path, "rb") as video_file:
                # Video notes are circular and limited to 60 seconds
                message = await bot.send_video_note(
                    chat_id=settings.telegram_channel_id,
                    video_note=video_file,
                )

            return PublishResult(
                success=True,
                platform_video_id=str(message.message_id),
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )
