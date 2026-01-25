import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.render_final import render_ffmpeg_kinetic
from app.services.media import probe_video


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_ffmpeg(tmp_path):
    audio = tmp_path / "audio.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100:d=8",
        str(audio),
    ]
    subprocess.run(cmd, check=True)

    ass = tmp_path / "captions.ass"
    ass.write_text("""[Script Info]\nTitle: Test\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,48,&H00FFFFFF,&H000000FF,&H66000000,&H66000000,0,0,0,0,100,100,0,0,1,2,0,2,80,80,120,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,0:00:08.00,Default,,0,0,0,,Тестовый титр\n""", encoding="utf-8")

    out = tmp_path / "video.mp4"
    render_ffmpeg_kinetic("Тест", str(ass), str(audio), str(out))
    info = probe_video(str(out))
    assert info.get("video_codec") == "h264"
    assert info.get("audio_codec") == "aac"
