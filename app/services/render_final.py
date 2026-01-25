import subprocess
from typing import List

from app.services.media import probe_duration


def render_ffmpeg_kinetic(
    hook: str,
    captions_ass: str,
    voiceover_path: str,
    output_path: str,
    min_duration: float = 8.0,
):
    duration = max(min_duration, probe_duration(voiceover_path))
    seg = duration / 3

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
        "text='{hook}':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=200:"
        "box=1:boxcolor=black@0.45:boxborderw=20:enable='lt(t,3)',"
        "subtitles='{ass}'[v];"
        "[3:a]volume=1.0[a1];"
        "[4:a]volume=0.3[a2];"
        "[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]"
    ).format(hook=escape_text(hook), ass=captions_ass)

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
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
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
