from elevenlabs.client import ElevenLabs
from app.core.config import settings
import os

class VoiceGenerator:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
    
    async def generate(self, text: str, output_path: str):
        audio = self.client.generate(
            text=text,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return output_path
