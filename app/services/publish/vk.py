import time
from typing import Dict

import httpx

from app.settings import settings


def publish_to_vk(video_path: str, title: str, description: str) -> Dict[str, str]:
    if not settings.VK_ACCESS_TOKEN or not settings.VK_GROUP_ID:
        raise ValueError("VK credentials missing")

    api_url = "https://api.vk.com/method"
    params = {
        "access_token": settings.VK_ACCESS_TOKEN,
        "v": settings.VK_API_VERSION,
        "group_id": settings.VK_GROUP_ID,
        "name": title,
        "description": description,
    }

    with httpx.Client(timeout=60) as client:
        save_resp = client.post(f"{api_url}/video.save", data=params)
        save_resp.raise_for_status()
        save_data = save_resp.json().get("response", {})
        upload_url = save_data.get("upload_url")
        video_id = save_data.get("video_id")
        owner_id = save_data.get("owner_id")
        if not upload_url:
            raise ValueError("upload_url missing")

        with open(video_path, "rb") as file_handle:
            upload_resp = client.post(upload_url, files={"video_file": file_handle})
        upload_resp.raise_for_status()

        attachment = f"video{owner_id}_{video_id}"
        wall_params = {
            "access_token": settings.VK_ACCESS_TOKEN,
            "v": settings.VK_API_VERSION,
            "owner_id": f"-{settings.VK_GROUP_ID}",
            "attachments": attachment,
            "message": description,
        }
        wall_resp = client.post(f"{api_url}/wall.post", data=wall_params)
        wall_resp.raise_for_status()

        for _ in range(10):
            status_params = {
                "access_token": settings.VK_ACCESS_TOKEN,
                "v": settings.VK_API_VERSION,
                "videos": attachment,
            }
            status_resp = client.post(f"{api_url}/video.get", data=status_params)
            status_resp.raise_for_status()
            items = status_resp.json().get("response", {}).get("items", [])
            if items and items[0].get("processing") == 0:
                break
            time.sleep(10)

    return {"video_id": str(video_id), "owner_id": str(owner_id), "attachment": attachment}
