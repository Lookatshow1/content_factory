"""
Subtitle Generator - Creates animated subtitles for videos.
Uses Whisper for transcription and FFmpeg for rendering.
"""
import os
import json
import uuid
import subprocess
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.core.config import settings


@dataclass
class SubtitleSegment:
    """A single subtitle segment."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Subtitle text


class SubtitleGenerator:
    """
    Generates and burns animated subtitles into videos.
    Modern TikTok-style animated captions.
    """

    # Subtitle styles presets
    STYLES = {
        "tiktok": {
            "font": "Montserrat-Bold",
            "fontsize": 60,
            "fontcolor": "white",
            "bordercolor": "black",
            "borderw": 4,
            "alignment": 10,  # Center bottom
        },
        "minimal": {
            "font": "Arial-Bold",
            "fontsize": 48,
            "fontcolor": "white",
            "bordercolor": "black@0.8",
            "borderw": 2,
            "alignment": 10,
        },
        "bold": {
            "font": "Impact",
            "fontsize": 72,
            "fontcolor": "yellow",
            "bordercolor": "black",
            "borderw": 5,
            "alignment": 10,
        },
    }

    def __init__(self):
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "ru",
    ) -> List[SubtitleSegment]:
        """
        Transcribe audio to subtitle segments using Whisper.

        Args:
            audio_path: Path to audio file
            language: Audio language code

        Returns:
            List of subtitle segments with timestamps
        """
        if not self.openai_client:
            raise ValueError("OPENAI_API_KEY not configured for transcription")

        with open(audio_path, "rb") as audio_file:
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

        # Convert words to segments (group by ~3-5 words)
        segments = []
        words = response.words if hasattr(response, 'words') else []

        if not words:
            # Fallback: use segment-level timestamps
            for segment in response.segments:
                segments.append(SubtitleSegment(
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"].strip(),
                ))
        else:
            # Group words into readable chunks
            current_words = []
            current_start = None

            for word in words:
                if current_start is None:
                    current_start = word["start"]

                current_words.append(word["word"])

                # Create segment every 4-6 words or at punctuation
                if (
                    len(current_words) >= 5
                    or word["word"].rstrip().endswith((".", "!", "?", ","))
                ):
                    segments.append(SubtitleSegment(
                        start=current_start,
                        end=word["end"],
                        text=" ".join(current_words).strip(),
                    ))
                    current_words = []
                    current_start = None

            # Don't forget remaining words
            if current_words:
                segments.append(SubtitleSegment(
                    start=current_start,
                    end=words[-1]["end"],
                    text=" ".join(current_words).strip(),
                ))

        return segments

    async def generate_from_script(
        self,
        script: str,
        audio_duration: float,
    ) -> List[SubtitleSegment]:
        """
        Generate subtitle segments from script text.
        Estimates timing based on audio duration.

        Args:
            script: The script text
            audio_duration: Total audio duration in seconds

        Returns:
            List of subtitle segments
        """
        # Split script into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', script.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Calculate timing
        total_chars = sum(len(s) for s in sentences)
        segments = []
        current_time = 0.0

        for sentence in sentences:
            # Duration proportional to character count
            duration = (len(sentence) / total_chars) * audio_duration
            # Ensure minimum duration
            duration = max(duration, 1.0)

            segments.append(SubtitleSegment(
                start=current_time,
                end=min(current_time + duration, audio_duration),
                text=sentence,
            ))
            current_time += duration

        return segments

    def segments_to_srt(
        self,
        segments: List[SubtitleSegment],
        output_path: str,
    ) -> str:
        """
        Convert segments to SRT subtitle file.

        Args:
            segments: List of subtitle segments
            output_path: Where to save the SRT file

        Returns:
            Path to SRT file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start_time = self._seconds_to_srt_time(segment.start)
                end_time = self._seconds_to_srt_time(segment.end)
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text}\n\n")

        return output_path

    def segments_to_ass(
        self,
        segments: List[SubtitleSegment],
        output_path: str,
        style: str = "tiktok",
    ) -> str:
        """
        Convert segments to ASS subtitle file with styling.
        ASS format allows for more advanced animations.

        Args:
            segments: List of subtitle segments
            output_path: Where to save the ASS file
            style: Style preset name

        Returns:
            Path to ASS file
        """
        style_config = self.STYLES.get(style, self.STYLES["tiktok"])
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        ass_content = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_config['font']},{style_config['fontsize']},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{style_config['borderw']},0,2,50,50,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        for segment in segments:
            start_time = self._seconds_to_ass_time(segment.start)
            end_time = self._seconds_to_ass_time(segment.end)
            # Add fade in/out effect
            text = f"{{\\fad(200,200)}}{segment.text}"
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return output_path

    async def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: Optional[str] = None,
        style: str = "tiktok",
    ) -> str:
        """
        Burn subtitles into video using FFmpeg.

        Args:
            video_path: Path to input video
            subtitle_path: Path to subtitle file (SRT or ASS)
            output_path: Where to save the output video
            style: Style preset (used if SRT)

        Returns:
            Path to output video
        """
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp4"
            output_path = os.path.join(settings.video_dir, filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Determine subtitle filter based on file type
        if subtitle_path.endswith(".ass"):
            subtitle_filter = f"ass='{subtitle_path}'"
        else:
            # SRT with inline styling
            style_config = self.STYLES.get(style, self.STYLES["tiktok"])
            subtitle_filter = (
                f"subtitles='{subtitle_path}':"
                f"force_style='FontName={style_config['font']},"
                f"FontSize={style_config['fontsize']},"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour=&H00000000,"
                f"BorderStyle=1,"
                f"Outline={style_config['borderw']},"
                f"Alignment=2,"
                f"MarginV=80'"
            )

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return output_path

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
