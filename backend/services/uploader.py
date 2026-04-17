from __future__ import annotations

from pathlib import Path
from typing import Iterator

import httpx

from backend.api.schemas import PrivacyStatus
from backend.core.config import Settings


class YouTubeUploader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _iter_file(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
        with path.open("rb") as handle:
            while chunk := handle.read(chunk_size):
                yield chunk

    def check_duplicate(self, access_token: str, title: str) -> dict[str, str | None]:
        response = httpx.get(
            "https://www.googleapis.com/youtube/v3/search",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"part": "snippet", "maxResults": 10, "q": title, "type": "video"},
            timeout=30,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        match = next(
            (
                item.get("snippet", {}).get("title")
                for item in items
                if item.get("snippet", {}).get("title", "").strip().lower() == title.strip().lower()
            ),
            None,
        )
        return {"status": "duplicate" if match else "clear", "matched_title": match}

    def upload_video(
        self,
        *,
        access_token: str,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: PrivacyStatus,
        thumbnail_path: Path | None = None,
    ) -> dict:
        metadata = {
            "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
            "status": {"privacyStatus": privacy_status.value},
        }
        with httpx.Client(timeout=None) as client:
            init_response = client.post(
                "https://www.googleapis.com/upload/youtube/v3/videos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Length": str(video_path.stat().st_size),
                    "X-Upload-Content-Type": "video/mp4",
                },
                params={"uploadType": "resumable", "part": "snippet,status"},
                json=metadata,
            )
            init_response.raise_for_status()
            upload_url = init_response.headers["Location"]
            upload_response = client.put(
                upload_url,
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "video/mp4"},
                content=self._iter_file(video_path),
            )
            upload_response.raise_for_status()
            payload = upload_response.json()
            if thumbnail_path and thumbnail_path.exists():
                with thumbnail_path.open("rb") as image_handle:
                    thumbnail_response = client.post(
                        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"videoId": payload["id"], "uploadType": "media"},
                        content=image_handle.read(),
                    )
                    thumbnail_response.raise_for_status()
        return payload
