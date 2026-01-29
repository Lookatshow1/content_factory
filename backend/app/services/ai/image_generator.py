"""
Image Generator using various AI services.
Generates images for video scenes.
"""
import os
import uuid
from typing import Optional
from pathlib import Path

import httpx

from app.core.config import settings


class ImageGenerator:
    """
    Generates images using AI services like DALL-E, Midjourney API, or FAL.ai.
    """

    # Using FAL.ai for image generation (Flux, Stable Diffusion, etc.)
    FAL_API_URL = "https://queue.fal.run"

    def __init__(self):
        self.fal_key = settings.fal_api_key

    def _get_proxy_config(self) -> dict:
        """Get proxy configuration for httpx."""
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
        if settings.https_proxy:
            proxies["https://"] = settings.https_proxy
        return proxies if proxies else None

    async def generate_image(
        self,
        prompt: str,
        style: str = "photorealistic",
        aspect_ratio: str = "9:16",
        output_path: Optional[str] = None,
        model: str = "fal-ai/flux/dev",  # or fal-ai/stable-diffusion-xl
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image
            style: Visual style (photorealistic, anime, illustration, etc.)
            aspect_ratio: Image aspect ratio
            output_path: Where to save the image
            model: AI model to use

        Returns:
            Path to generated image
        """
        if not self.fal_key:
            raise ValueError("FAL_API_KEY not configured")

        # Enhance prompt with style
        full_prompt = self._build_prompt(prompt, style)

        # Get dimensions
        width, height = self._get_dimensions(aspect_ratio)

        # Submit request
        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(timeout=120.0, proxy=proxy_config) as client:
            response = await client.post(
                f"{self.FAL_API_URL}/{model}",
                headers={
                    "Authorization": f"Key {self.fal_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": full_prompt,
                    "image_size": {
                        "width": width,
                        "height": height,
                    },
                    "num_images": 1,
                    "enable_safety_checker": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        # Get image URL
        image_url = data["images"][0]["url"]

        # Download image
        if output_path is None:
            filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(settings.media_dir, "images", filename)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await self._download_file(image_url, output_path)

        return output_path

    async def generate_scene_images(
        self,
        script_segments: list[str],
        base_prompt: Optional[str] = None,
        style: str = "cinematic",
        aspect_ratio: str = "9:16",
    ) -> list[dict]:
        """
        Generate images for multiple script segments.

        Args:
            script_segments: List of script text segments
            base_prompt: Base prompt to add to all images
            style: Visual style
            aspect_ratio: Image aspect ratio

        Returns:
            List of dicts with segment, prompt, and image_path
        """
        results = []

        for i, segment in enumerate(script_segments):
            # Generate prompt from segment
            prompt = await self._segment_to_prompt(segment, base_prompt)

            try:
                image_path = await self.generate_image(
                    prompt=prompt,
                    style=style,
                    aspect_ratio=aspect_ratio,
                )
                results.append({
                    "index": i,
                    "segment": segment,
                    "prompt": prompt,
                    "image_path": image_path,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "segment": segment,
                    "prompt": prompt,
                    "image_path": None,
                    "success": False,
                    "error": str(e),
                })

        return results

    async def regenerate_scene_image(
        self,
        prompt: str,
        style: str = "cinematic",
        aspect_ratio: str = "9:16",
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Regenerate a specific scene image with optional custom prompt.

        Args:
            prompt: Original prompt
            style: Visual style
            aspect_ratio: Image aspect ratio
            custom_prompt: Override prompt if provided

        Returns:
            Path to new image
        """
        final_prompt = custom_prompt or prompt
        return await self.generate_image(
            prompt=final_prompt,
            style=style,
            aspect_ratio=aspect_ratio,
        )

    async def _segment_to_prompt(
        self,
        segment: str,
        base_prompt: Optional[str] = None,
    ) -> str:
        """
        Convert a script segment to an image prompt using AI.
        """
        # Use OpenRouter to generate image prompt from script
        if settings.openrouter_api_key:
            prompt_request = f"""Convert this script segment into a detailed image generation prompt.
The image should visually represent the content being discussed.

Script: "{segment}"

{"Base style/context: " + base_prompt if base_prompt else ""}

Return ONLY the image prompt, nothing else. Make it detailed and visually descriptive.
Focus on: scene, lighting, composition, mood, specific visual elements."""

            proxy_config = self._get_proxy_config()
            async with httpx.AsyncClient(timeout=60.0, proxy=proxy_config) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt_request}],
                        "max_tokens": 300,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

        # Fallback: just use the segment with base prompt
        if base_prompt:
            return f"{base_prompt}. Scene depicting: {segment}"
        return f"Cinematic scene depicting: {segment}"

    def _build_prompt(self, prompt: str, style: str) -> str:
        """Build full prompt with style modifiers."""
        style_modifiers = {
            "photorealistic": "photorealistic, highly detailed, 8k, professional photography",
            "cinematic": "cinematic, movie still, dramatic lighting, film grain, anamorphic",
            "anime": "anime style, vibrant colors, detailed illustration, studio ghibli inspired",
            "illustration": "digital illustration, detailed artwork, professional illustration",
            "3d_render": "3D render, octane render, detailed, realistic lighting",
            "minimalist": "minimalist, clean, simple, modern design",
        }

        modifier = style_modifiers.get(style, style_modifiers["cinematic"])
        return f"{prompt}, {modifier}"

    def _get_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        """Get pixel dimensions for aspect ratio."""
        dimensions = {
            "9:16": (720, 1280),   # Vertical/Shorts
            "16:9": (1280, 720),   # Horizontal
            "1:1": (1024, 1024),   # Square
            "4:3": (1024, 768),
            "3:4": (768, 1024),
        }
        return dimensions.get(aspect_ratio, (720, 1280))

    async def _download_file(self, url: str, output_path: str):
        """Download a file from URL."""
        proxy_config = self._get_proxy_config()
        async with httpx.AsyncClient(proxy=proxy_config) as client:
            response = await client.get(url, timeout=60)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)
