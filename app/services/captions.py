from pathlib import Path
from typing import List, Tuple

from app.services.media import probe_duration


def _format_srt_time(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours = millis // 3600000
    minutes = (millis % 3600000) // 60000
    secs = (millis % 60000) // 1000
    ms = millis % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _format_ass_time(seconds: float) -> str:
    total = int(seconds * 100)
    hours = total // 360000
    minutes = (total % 360000) // 6000
    secs = (total % 6000) // 100
    cs = total % 100
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{cs:02d}"


def generate_srt(captions: List[str], audio_path: str, output_path: str) -> float:
    duration = probe_duration(audio_path)
    count = max(1, len(captions))
    segment = duration / count
    lines = []
    for idx, line in enumerate(captions):
        start = idx * segment
        end = (idx + 1) * segment
        lines.append(str(idx + 1))
        lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        lines.append(line)
        lines.append("")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    return duration


def generate_ass(captions: List[str], audio_path: str, output_path: str) -> float:
    duration = probe_duration(audio_path)
    count = max(1, len(captions))
    segment = duration / count
    header = """[Script Info]
Title: SVF Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,48,&H00FFFFFF,&H000000FF,&H66000000,&H66000000,0,0,0,0,100,100,0,0,1,2,0,2,120,120,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for idx, line in enumerate(captions):
        start = idx * segment
        end = (idx + 1) * segment
        events.append(
            f"Dialogue: 0,{_format_ass_time(start)},{_format_ass_time(end)},Default,,0,0,0,,{line}"
        )
    Path(output_path).write_text(header + "\n" + "\n".join(events), encoding="utf-8")
    return duration


def generate_captions(captions: List[str], audio_path: str, base_path: str) -> Tuple[str, str, float]:
    srt_path = f"{base_path}.srt"
    ass_path = f"{base_path}.ass"
    duration = generate_srt(captions, audio_path, srt_path)
    generate_ass(captions, audio_path, ass_path)
    return srt_path, ass_path, duration
