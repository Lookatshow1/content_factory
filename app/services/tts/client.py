import subprocess
from pathlib import Path
from typing import Dict, Optional

import httpx

from app import crud
from app.db import SessionLocal
from app.services.script import count_words
from app.settings import settings


class TTSClient:
    def __init__(self, job_id=None):
        self.job_id = job_id
        self.provider = (settings.TTS_PROVIDER or "stub").lower()

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> Dict[str, str]:
        if self.provider != "elevenlabs":
            return self._stub_tts(text)
        return self._elevenlabs_tts(text, voice_id)

    def _stub_tts(self, text: str) -> Dict[str, str]:
        words = count_words(text)
        duration = max(8.0, min(12.0, words / 2.8))
        output_path = Path(f"/tmp/voice_{self.job_id}_stub.wav")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=channel_layout=stereo:sample_rate=44100:d={duration}",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)
        return {"path": str(output_path), "voice_id": "stub", "provider": "stub"}

    def _elevenlabs_tts(self, text: str, voice_id: Optional[str]) -> Dict[str, str]:
        api_key = settings.ELEVENLABS_API_KEY
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY missing")
        base_url = settings.ELEVENLABS_BASE_URL.rstrip("/")
        voice_id = voice_id or settings.ELEVENLABS_VOICE_ID or self._get_or_select_voice(api_key, base_url)

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": settings.ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": settings.ELEVENLABS_STABILITY,
                "similarity_boost": settings.ELEVENLABS_SIMILARITY,
            },
        }
        out_raw = Path(f"/tmp/voice_{self.job_id}.mp3")
        out_norm = Path(f"/tmp/voice_{self.job_id}_norm.wav")
        url = f"{base_url}/text-to-speech/{voice_id}"
        with httpx.Client(timeout=settings.TTS_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            out_raw.write_bytes(response.content)

        self._loudnorm(out_raw, out_norm)
        return {"path": str(out_norm), "voice_id": voice_id, "provider": "elevenlabs"}

    def _loudnorm(self, input_path: Path, output_path: Path):
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)

    def _get_or_select_voice(self, api_key: str, base_url: str) -> str:
        session = SessionLocal()
        try:
            setting = crud.get_setting(session, "elevenlabs_voice_id")
            if setting and setting.value_json:
                return setting.value_json.get("voice_id")

            headers = {"xi-api-key": api_key}
            url = f"{base_url}/voices"
            with httpx.Client(timeout=settings.TTS_TIMEOUT) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            voices = data.get("voices", [])
            if not voices:
                raise ValueError("No voices available")
            voice_id = voices[0]["voice_id"]
            crud.set_setting(session, "elevenlabs_voice_id", {"voice_id": voice_id})
            return voice_id
        finally:
            session.close()
