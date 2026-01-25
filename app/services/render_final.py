import subprocess
from typing import List

from app.services.media import probe_duration


def wrap_text(text: str, max_chars: int = 24, max_lines: int = 3) -> str:
    words = (text or "").split()
    if not words:
        return ""
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if not lines[-1].endswith("..."):
            lines[-1] = lines[-1].rstrip(".") + "..."
    return "\n".join(lines)


def render_ffmpeg_kinetic(
    hook: str,
    captions_ass: str,
    voiceover_path: str,
    output_path: str,
    min_duration: float = 8.0,
):
    duration = max(min_duration, probe_duration(voiceover_path))
    seg = duration / 3
    hook_wrapped = wrap_text(hook, max_chars=24, max_lines=3)

    colors = ["#111111", "#1a1a1a", "#222222"]
    inputs = []
    for color in colors:
        inputs.extend(["-f", "lavfi", "-i", f"color=c={color}:s=1080x1920:d={seg}:r=30"])

    inputs.extend(["-i", voiceover_path])
    inputs.extend(["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.002:d={duration}"])

    filter_complex = (
        "[0:v][1:v][2:v]concat=n=3:v=1:a=0,"
        "format=yuv420p,"
        "zoompan=z='min(zoom+0.0006,1.04)':d=1:s=1080x1920:fps=30"
        "[vbase];"
        "[vbase]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='{hook}':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=170:"
        "box=1:boxcolor=black@0.45:boxborderw=20:line_spacing=10:enable='lt(t,3)',"
        "subtitles='{ass}'[v];"
        "[3:a]volume=1.0[a1];"
        "[4:a]volume=0.3[a2];"
        "[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]"
    ).format(hook=escape_text(hook_wrapped), ass=captions_ass)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "[a]",
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
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def escape_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("\n", "\\n")
    )
