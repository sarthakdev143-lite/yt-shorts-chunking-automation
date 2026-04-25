from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.schemas import ChunkStatus, YouTubeDuplicateCheckRequest, YouTubeUploadRequest
from backend.core.config import get_settings
from backend.services.repository import get_repository
from backend.services.uploader import YouTubeUploader

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.post("/duplicate-check")
def duplicate_check(request: YouTubeDuplicateCheckRequest) -> dict[str, str | None]:
    settings = get_settings()
    if settings.demo_mode:
        return {"status": "checking", "matched_title": None}
    return YouTubeUploader(settings).check_duplicate(request.access_token, request.title)


@router.post("/upload")
def upload_chunk(request: YouTubeUploadRequest) -> dict:
    settings = get_settings()
    repository = get_repository()
    project = repository.find_project_by_chunk(request.chunk_id)
    if not project:
        raise HTTPException(status_code=404, detail="Chunk not found")
    chunk = next((item for item in project.chunks if item.id == request.chunk_id), None)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    if settings.demo_mode:
        chunk.status = ChunkStatus.UPLOADED
        chunk.youtube_video_id = f"yt_{chunk.id}"
        chunk.upload_attempts += 1
        repository.save_project(project)
        return {"status": "demo-uploaded", "videoId": chunk.youtube_video_id}
    raise HTTPException(status_code=501, detail="Live upload is delegated to the worker-managed artifact pipeline.")
