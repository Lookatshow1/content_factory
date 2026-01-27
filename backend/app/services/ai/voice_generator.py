"""
Voice Generator using ElevenLabs API.
Generates natural voiceovers for video scripts.
"""
import os
import uuid
from typing import Optional
from pathlib import Path

from elevenlabs import ElevenLabs, VoiceSettings

from app.core.config import settings


class VoiceGenerator:
    """
    Generates voiceovers using ElevenLabs text-to-speech.
    Supports voice cloning and multiple languages.
    """

    # Recommended voices for different content types
    VOICE_PRESETS = {
        "professional_male": "ErXwobaYiN019PkySvjV",  # Antoni
        "professional_female": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "energetic_male": "TxGEqnHWrfWFTfGW9XjX",  # Josh
        "energetic_female": "EXAVITQu4vr4xnSDxMaL",  # Bella
        "casual_male": "pNInz6obpgDQGcFmaJgB",  # Adam
        "casual_female": "MF3mGyEYCl7XYWbV9V6O",  # Elli
    }

    def __init__(self):
        if not settings.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    async def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speed: float = 1.0,
    ) -> str:
        """
        Generate voiceover from text.

        Args:
            text: Script text to convert to speech
            voice_id: ElevenLabs voice ID (or preset name)
            output_path: Where to save the audio file
            stability: Voice stability (0-1)
            similarity_boost: How closely to match voice (0-1)
            style: Style exaggeration (0-1)
            speed: Speech speed multiplier

        Returns:
            Path to generated audio file
        """
        # Resolve voice ID
        if voice_id is None:
            voice_id = settings.default_voice_id
        elif voice_id in self.VOICE_PRESETS:
            voice_id = self.VOICE_PRESETS[voice_id]

        # Generate output path if not provided
        if output_path is None:
            filename = f"{uuid.uuid4()}.mp3"
            output_path = os.path.join(settings.audio_dir, filename)

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Clean up script markers
        clean_text = self._prepare_text(text)

        # Generate audio
        audio_generator = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=clean_text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
            ),
        )

        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)

        return output_path

    def _prepare_text(self, text: str) -> str:
        """
        Prepare script text for TTS.
        Converts [PAUSE] markers to SSML breaks, etc.
        """
        # Replace pause markers with actual pauses
        # ElevenLabs interprets "..." as natural pauses
        text = text.replace("[PAUSE]", "...")
        text = text.replace("[pause]", "...")

        # Remove any remaining markers
        import re
        text = re.sub(r'\[.*?\]', '', text)

        return text.strip()

    async def get_voices(self) -> list[dict]:
        """
        Get list of available voices.

        Returns:
            List of voice info dicts
        """
        response = self.client.voices.get_all()
        return [
            {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "labels": voice.labels,
            }
            for voice in response.voices
        ]

    async def clone_voice(
        self,
        name: str,
        audio_files: list[str],
        description: Optional[str] = None,
    ) -> str:
        """
        Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            audio_files: List of paths to audio samples
            description: Description of the voice

        Returns:
            Voice ID of the cloned voice
        """
        files = []
        for path in audio_files:
            with open(path, "rb") as f:
                files.append(f.read())

        response = self.client.voices.add(
            name=name,
            description=description or f"Cloned voice: {name}",
            files=files,
        )

        return response.voice_id

    async def get_audio_duration(self, audio_path: str) -> float:
        """
        Get duration of an audio file in seconds.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        import subprocess
        import json

        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                audio_path,
            ],
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
