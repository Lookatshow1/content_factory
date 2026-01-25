import json
import subprocess
from typing import Dict


def probe_duration(path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def probe_video(path: str) -> Dict[str, str]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        path,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        if stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream
    return {
        "width": str(video_stream.get("width")) if video_stream else "",
        "height": str(video_stream.get("height")) if video_stream else "",
        "video_codec": video_stream.get("codec_name") if video_stream else "",
        "audio_codec": audio_stream.get("codec_name") if audio_stream else "",
        "has_video": "1" if video_stream else "0",
        "has_audio": "1" if audio_stream else "0",
    }
