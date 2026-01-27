"""
Video Processor - Final video assembly and processing.
Combines all elements: video, audio, subtitles, effects.
"""
import os
import uuid
import subprocess
import json
from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class VideoMetadata:
    """Video file metadata."""
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    bitrate: int


class VideoProcessor:
    """
    Handles final video processing:
    - Combining video + audio
    - Adding effects and transitions
    - Optimizing for different platforms
    - Generating thumbnails
    """

    # Platform-specific encoding presets
    PLATFORM_PRESETS = {
        "youtube": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "8M",
            "audio_bitrate": "256k",
            "preset": "slow",
            "crf": 18,
        },
        "tiktok": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "4M",
            "audio_bitrate": "128k",
            "preset": "medium",
            "crf": 23,
        },
        "instagram": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "5M",
            "audio_bitrate": "128k",
            "preset": "medium",
            "crf": 22,
        },
        "vk": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "4M",
            "audio_bitrate": "128k",
            "preset": "medium",
            "crf": 23,
        },
        "telegram": {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "2M",
            "audio_bitrate": "128k",
            "preset": "fast",
            "crf": 26,
        },
    }

    async def get_metadata(self, video_path: str) -> VideoMetadata:
        """
        Get video file metadata using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {result.stderr}")

        data = json.loads(result.stdout)
        video_stream = next(
            (s for s in data["streams"] if s["codec_type"] == "video"),
            None
        )

        if not video_stream:
            raise ValueError("No video stream found")

        # Parse framerate
        fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

        return VideoMetadata(
            duration=float(data["format"].get("duration", 0)),
            width=int(video_stream.get("width", 1080)),
            height=int(video_stream.get("height", 1920)),
            fps=fps,
            codec=video_stream.get("codec_name", "unknown"),
            bitrate=int(data["format"].get("bit_rate", 0)),
        )

    async def combine_video_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Combine video with audio track.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Where to save output

        Returns:
            Path to combined video
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def add_background_music(
        self,
        video_path: str,
        music_path: str,
        volume: float = 0.1,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Add background music to video.

        Args:
            video_path: Path to video with main audio
            music_path: Path to background music
            volume: Music volume (0.0 - 1.0)
            output_path: Where to save output

        Returns:
            Path to output video
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Mix audio tracks
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            f"[0:a]volume=1.0[a1];[1:a]volume={volume}[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def optimize_for_platform(
        self,
        video_path: str,
        platform: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Optimize video encoding for specific platform.

        Args:
            video_path: Path to input video
            platform: Target platform (youtube, tiktok, etc.)
            output_path: Where to save output

        Returns:
            Path to optimized video
        """
        preset = self.PLATFORM_PRESETS.get(platform, self.PLATFORM_PRESETS["tiktok"])

        if output_path is None:
            filename = f"{uuid.uuid4()}_{platform}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-c:v", preset["video_codec"],
            "-b:v", preset["video_bitrate"],
            "-preset", preset["preset"],
            "-crf", str(preset["crf"]),
            "-c:a", preset["audio_codec"],
            "-b:a", preset["audio_bitrate"],
            "-movflags", "+faststart",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def generate_thumbnail(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        timestamp: float = 1.0,
    ) -> str:
        """
        Generate thumbnail from video frame.

        Args:
            video_path: Path to video
            output_path: Where to save thumbnail
            timestamp: Timestamp in seconds to capture

        Returns:
            Path to thumbnail
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.jpg"
            output_path = os.path.join(settings.thumbnail_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def trim_video(
        self,
        video_path: str,
        start: float,
        end: float,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Trim video to specific time range.

        Args:
            video_path: Path to video
            start: Start time in seconds
            end: End time in seconds
            output_path: Where to save output

        Returns:
            Path to trimmed video
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        duration = end - start
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(duration),
            "-c", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def add_intro_outro(
        self,
        video_path: str,
        intro_path: Optional[str] = None,
        outro_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Add intro and/or outro to video.

        Args:
            video_path: Main video path
            intro_path: Intro video path (optional)
            outro_path: Outro video path (optional)
            output_path: Where to save output

        Returns:
            Path to final video
        """
        if not intro_path and not outro_path:
            return video_path

        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Build concat file
        concat_file = os.path.join(settings.temp_dir, f"{uuid.uuid4()}.txt")
        with open(concat_file, "w") as f:
            if intro_path:
                f.write(f"file '{intro_path}'\n")
            f.write(f"file '{video_path}'\n")
            if outro_path:
                f.write(f"file '{outro_path}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        os.remove(concat_file)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    async def resize_for_vertical(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        target_width: int = 1080,
        target_height: int = 1920,
    ) -> str:
        """
        Resize/crop video to vertical format.

        Args:
            video_path: Input video
            output_path: Where to save output
            target_width: Target width (default 1080)
            target_height: Target height (default 1920)

        Returns:
            Path to resized video
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Scale and pad to maintain aspect ratio
        filter_complex = (
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path
