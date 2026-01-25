from typing import Dict

from app.settings import settings


def publish_to_tiktok(video_path: str, title: str) -> Dict[str, str]:
    if not settings.TIKTOK_ACCESS_TOKEN:
        raise ValueError("TIKTOK_ACCESS_TOKEN missing")

    return {
        "status": "manual_required",
        "note": "TikTok direct post требует аудит. Загрузите вручную через кабинет.",
        "video_path": video_path,
        "title": title,
    }
