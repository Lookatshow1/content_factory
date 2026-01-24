import subprocess
from pathlib import Path
from typing import List


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("\n", "\\n")
    )


def render_clip_stub(hook: str, captions: List[str], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    caption_lines = captions[:2] if captions else []
    caption_text = "\\n".join(caption_lines)

    hook_text = _escape(hook)
    caption_text = _escape(caption_text)

    draw_hook = (
        "drawtext="
        f"fontfile={FONT_PATH}:"
        f"text='{hook_text}':"
        "fontcolor=white:fontsize=80:"
        "x=(w-text_w)/2:y=220:"
        "box=1:boxcolor=black@0.4:boxborderw=24"
    )

    draw_caption = (
        "drawtext="
        f"fontfile={FONT_PATH}:"
        f"text='{caption_text}':"
        "fontcolor=white:fontsize=48:"
        "x=(w-text_w)/2:y=980:"
        "line_spacing=10:"
        "box=1:boxcolor=black@0.4:boxborderw=16"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=#1b1b1b:s=1080x1920:d=8",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf",
        f"{draw_hook},{draw_caption}",
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(out),
    ]

    subprocess.run(cmd, check=True)
