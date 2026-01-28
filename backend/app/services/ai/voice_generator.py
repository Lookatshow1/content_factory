"""
Voice Generator using ElevenLabs API.
Generates natural voiceovers for video scripts.
"""
import os
import uuid
import re
from typing import Optional
from pathlib import Path

import httpx

from app.core.config import settings


class VoiceGenerator:
    """
    Generates voiceovers using ElevenLabs text-to-speech.
    Supports voice cloning and multiple languages.
    """

    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

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
        self.api_key = settings.elevenlabs_api_key

    def _get_proxy_config(self) -> dict:
        """Get proxy configuration for httpx."""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        return proxies if proxies else None

    def _get_headers(self) -> dict:
        """Get API headers."""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

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

        # Prepare request
        url = f"{self.ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        payload = {
            "text": clean_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
            }
        }

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=180.0, proxy=proxy_config) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()

            # Save audio to file
            with open(output_path, "wb") as f:
                f.write(response.content)

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
        text = re.sub(r'\[.*?\]', '', text)

        return text.strip()

    async def get_voices(self) -> list[dict]:
        """
        Get list of available voices.

        Returns:
            List of voice info dicts
        """
        url = f"{self.ELEVENLABS_API_URL}/voices"

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=30.0, proxy=proxy_config) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

        return [
            {
                "voice_id": voice["voice_id"],
                "name": voice["name"],
                "category": voice.get("category"),
                "labels": voice.get("labels", {}),
            }
            for voice in data.get("voices", [])
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
        url = f"{self.ELEVENLABS_API_URL}/voices/add"

        # Prepare multipart form data
        files = []
        for path in audio_files:
            with open(path, "rb") as f:
                files.append(("files", (os.path.basename(path), f.read(), "audio/mpeg")))

        data = {
            "name": name,
            "description": description or f"Cloned voice: {name}",
        }

        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=120.0, proxy=proxy_config) as client:
            response = await client.post(
                url,
                headers={"xi-api-key": self.api_key},
                data=data,
                files=files
            )
            response.raise_for_status()
            result = response.json()

        return result["voice_id"]

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
