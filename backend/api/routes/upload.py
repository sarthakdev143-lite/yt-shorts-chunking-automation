from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter

from backend.api.schemas import CompleteUploadRequest, PresignUploadRequest, PresignUploadResponse, Project, ProjectStatus
from backend.services.events import get_event_broker
from backend.services.repository import get_repository
from backend.services.storage import StorageService
from backend.workers.tasks import enqueue_processing
from backend.core.config import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or uuid4().hex[:10]


@router.post("/presign", response_model=PresignUploadResponse)
def presign_upload(request: PresignUploadRequest) -> PresignUploadResponse:
    settings = get_settings()
    storage = StorageService(settings)
    object_key = f"uploads/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_slugify(request.project_name)}-{request.filename}"

    if not storage.ready:
        return PresignUploadResponse(url="https://demo-r2.invalid/presigned-upload", method="PUT", objectKey=object_key, publicUrl=None)

    return PresignUploadResponse.model_validate(storage.generate_presigned_upload(object_key, request.content_type))


@router.post("/complete", response_model=Project)
async def complete_upload(request: CompleteUploadRequest) -> Project:
    repository = get_repository()
    broker = get_event_broker()
    now = datetime.now(timezone.utc).isoformat()
    project = Project(
        id=f"proj_{_slugify(request.project_name)}",
        name=request.project_name,
        status=ProjectStatus.PROCESSING,
        privacy=request.privacy,
        chunkDuration=request.chunk_duration,
        sceneDetection=request.scene_detection,
        sourceVideoKey=request.object_key,
        sourceVideoUrl="/demo/short-placeholder.mp4",
        createdAt=now,
        updatedAt=now,
        uploadProgress=4,
        processingStage="Upload completed, awaiting chunk processing",
        queueDepth=1,
        channelName="Connected YouTube channel",
        scheduleMode="interval",
        dailyIntervalHours=24,
        descriptionTemplate="Generated from uploaded source footage.",
        chunks=[],
    )
    repository.save_project(project)
    repository.append_activity(f"Queued {project.name} for processing", kind="storage")
    await broker.publish(project.id, kind="queue", message="Upload complete, dispatching worker")
    enqueue_processing(project.id, request.object_key)
    return project
