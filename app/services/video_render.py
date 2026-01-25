import subprocess
import time
from pathlib import Path
from typing import Dict

import httpx

from app.services.media import probe_video
from app.services.render_final import render_ffmpeg_kinetic, escape_text, wrap_text
from app.settings import settings


def render_clip(job_id: str, hook: str, captions_ass: str, voiceover_path: str, output_path: str) -> Dict[str, str]:
    if settings.VIDEO_BACKEND == "heygen" and settings.HEYGEN_API_KEY:
        base = f"/tmp/{job_id}_heygen.mp4"
        result = render_heygen_avatar(job_id, hook, voiceover_path, base)
        overlay_captions(base, hook, captions_ass, output_path)
        result["path"] = output_path
        return result
    render_ffmpeg_kinetic(hook, captions_ass, voiceover_path, output_path)
    return {"path": output_path, "backend": "ffmpeg"}


def render_heygen_avatar(job_id: str, hook: str, voiceover_path: str, output_path: str) -> Dict[str, str]:
    api_key = settings.HEYGEN_API_KEY
    if not api_key:
        raise ValueError("HEYGEN_API_KEY missing")
    base_url = settings.HEYGEN_BASE_URL.rstrip("/")

    payload = {
        "video_inputs": [
            {
                "voice": {"audio_url": None},
                "script": hook,
            }
        ],
        "test": False,
    }
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    with httpx.Client(timeout=60) as client:
        response = client.post(f"{base_url}/v2/video/generate", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        video_id = data.get("data", {}).get("video_id") or data.get("video_id")
        if not video_id:
            raise ValueError("heygen video_id missing")

        for _ in range(settings.HEYGEN_MAX_POLLS):
            status_resp = client.get(
                f"{base_url}/v2/video/status/{video_id}",
                headers=headers,
            )
            if status_resp.status_code >= 400:
                time.sleep(settings.HEYGEN_POLL_INTERVAL)
                continue
            status_data = status_resp.json().get("data", status_resp.json())
            status = status_data.get("status")
            if status in ("completed", "done"):
                url = status_data.get("video_url") or status_data.get("url")
                if not url:
                    raise ValueError("heygen video_url missing")
                video_bytes = client.get(url).content
                Path(output_path).write_bytes(video_bytes)
                return {"path": output_path, "backend": "heygen", "video_id": video_id}
            if status in ("failed", "error"):
                raise ValueError("heygen render failed")
            time.sleep(settings.HEYGEN_POLL_INTERVAL)

    raise TimeoutError("heygen render timeout")


def validate_final_video(path: str) -> Dict[str, str]:
    info = probe_video(path)
    if info.get("width") != "1080" or info.get("height") != "1920":
        raise ValueError("invalid resolution")
    if info.get("video_codec") != "h264":
        raise ValueError("invalid video codec")
    if info.get("audio_codec") != "aac":
        raise ValueError("invalid audio codec")
    return info


def overlay_captions(input_path: str, hook: str, ass_path: str, output_path: str):
    hook_wrapped = wrap_text(hook, max_chars=24, max_lines=3)
    draw = (
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        f"text='{escape_text(hook_wrapped)}':fontcolor=white:fontsize=68:"
        "x=(w-text_w)/2:y=170:box=1:boxcolor=black@0.45:boxborderw=16:line_spacing=8"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        f"{draw},subtitles='{ass_path}'",
        "-c:v",
        "libx264",
        "-preset",
        "veryslow",
        "-b:v",
        "8M",
        "-minrate",
        "8M",
        "-maxrate",
        "8M",
        "-bufsize",
        "16M",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-ar",
        "48000",
        output_path,
    ]
    subprocess.run(cmd, check=True)
