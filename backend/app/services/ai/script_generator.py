"""
Script Generator using Claude API.
Generates viral short-form video scripts optimized for engagement.
"""
import json
import re
from typing import Optional
from dataclasses import dataclass

import anthropic

from app.core.config import settings


@dataclass
class GeneratedScript:
    """Result of script generation."""
    title: str
    description: str
    script: str
    hashtags: list[str]
    hook: str  # First 3 seconds hook
    cta: str   # Call to action


class ScriptGenerator:
    """
    Generates engaging short-form video scripts using Claude.
    Optimized for viral content on TikTok, Reels, Shorts, etc.
    """

    SYSTEM_PROMPT = """You are an expert viral content creator specializing in short-form vertical videos.
Your scripts are known for:
- Powerful hooks that grab attention in the first 2-3 seconds
- High engagement and watch-through rates
- Clear, punchy delivery optimized for voiceover
- Emotional resonance and shareability
- Strategic use of trending topics and formats

You write scripts for 30-60 second videos that feel authentic and engaging.
Your content is educational, entertaining, or inspiring - never boring.

IMPORTANT RULES:
1. Start with a HOOK - a provocative question, shocking fact, or bold statement
2. Keep sentences SHORT and punchy - each one should hit hard
3. Use conversational language - like talking to a friend
4. Build tension and deliver value
5. End with a clear call-to-action
6. No emojis in the script (they'll be added separately)
7. Write for SPEAKING, not reading - use natural speech patterns
8. Include strategic pauses marked with [PAUSE]
9. Duration target: script should take about {duration} seconds to read aloud"""

    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def generate(
        self,
        topic: str,
        niche: str = "technology",
        style: str = "educational",
        tone: str = "professional",
        duration_seconds: int = 45,
        language: str = "ru",
    ) -> GeneratedScript:
        """
        Generate a complete video script.

        Args:
            topic: Main topic for the video
            niche: Content niche (technology, business, lifestyle, etc.)
            style: Video style (educational, entertaining, motivational, etc.)
            tone: Tone of voice (professional, casual, energetic, etc.)
            duration_seconds: Target duration
            language: Script language (ru, en, etc.)

        Returns:
            GeneratedScript with all content pieces
        """
        user_prompt = f"""Create a viral short-form video script with these parameters:

TOPIC: {topic}
NICHE: {niche}
STYLE: {style}
TONE: {tone}
DURATION: {duration_seconds} seconds
LANGUAGE: {"Russian" if language == "ru" else "English"}

Generate a complete script package in JSON format:
{{
    "title": "Catchy video title (max 100 chars)",
    "description": "Engaging description for social media (2-3 sentences)",
    "hook": "The attention-grabbing first line (first 3 seconds)",
    "script": "The complete voiceover script with [PAUSE] markers",
    "cta": "Call to action at the end",
    "hashtags": ["relevant", "trending", "hashtags", "for", "discovery"]
}}

Make it VIRAL. Make it ENGAGING. Make people want to share it."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=self.SYSTEM_PROMPT.format(duration=duration_seconds),
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Parse the response
        content = response.content[0].text

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if not json_match:
            raise ValueError("Failed to parse script JSON from Claude response")

        data = json.loads(json_match.group())

        return GeneratedScript(
            title=data.get("title", f"Video about {topic}"),
            description=data.get("description", ""),
            script=data.get("script", ""),
            hashtags=data.get("hashtags", []),
            hook=data.get("hook", ""),
            cta=data.get("cta", ""),
        )

    async def improve_script(
        self,
        original_script: str,
        feedback: str,
    ) -> str:
        """
        Improve an existing script based on feedback.

        Args:
            original_script: The script to improve
            feedback: What to improve

        Returns:
            Improved script
        """
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Improve this video script based on the feedback.

ORIGINAL SCRIPT:
{original_script}

FEEDBACK:
{feedback}

Return ONLY the improved script, nothing else.""",
                }
            ],
        )

        return response.content[0].text

    async def generate_hashtags(
        self,
        topic: str,
        niche: str,
        platform: str = "tiktok",
        count: int = 10,
    ) -> list[str]:
        """
        Generate optimized hashtags for a video.

        Args:
            topic: Video topic
            niche: Content niche
            platform: Target platform
            count: Number of hashtags to generate

        Returns:
            List of hashtags (without #)
        """
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate {count} highly effective hashtags for a {platform} video.

TOPIC: {topic}
NICHE: {niche}

Requirements:
- Mix of popular and niche-specific hashtags
- Include trending hashtags if relevant
- No # symbol, just the tag text
- Optimized for discoverability

Return ONLY the hashtags, one per line, no explanations.""",
                }
            ],
        )

        hashtags = response.content[0].text.strip().split("\n")
        return [tag.strip().lstrip("#") for tag in hashtags if tag.strip()][:count]
