from __future__ import annotations

import mimetypes
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.schemas import PrivacyStatus, Project, ProjectStatus, SourceUrlIngestRequest
from backend.services.events import get_event_broker
from backend.services.downloader import SourceDownloader
from backend.services.repository import get_repository
from backend.services.storage import StorageService
from backend.workers.tasks import enqueue_processing
from backend.core.config import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])
VIDEO_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-matroska", "video/webm", "video/x-msvideo"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or uuid4().hex[:10]


def _validated_upload_content_type(file: UploadFile) -> str:
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    if content_type not in VIDEO_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only common video uploads are supported.")
    return content_type


async def _persist_upload_to_path(file: UploadFile, destination: Path, max_bytes: int) -> str:
    content_type = _validated_upload_content_type(file)

    total_bytes = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        while chunk := await file.read(UPLOAD_CHUNK_SIZE):
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise HTTPException(status_code=413, detail=f"Upload exceeds the {max_bytes // (1024 * 1024)} MB limit.")
            handle.write(chunk)

    await file.close()
    if total_bytes == 0:
        raise HTTPException(status_code=400, detail="Uploaded file was empty.")
    return content_type


async def _queue_project(
    *,
    object_key: str,
    project_name: str,
    chunk_duration: int,
    scene_detection: bool,
    privacy: PrivacyStatus,
    source_video_url: str,
) -> Project:
    repository = get_repository()
    broker = get_event_broker()
    now = datetime.now(timezone.utc).isoformat()
    project = Project(
        id=f"proj_{_slugify(project_name)}",
        name=project_name,
        status=ProjectStatus.PROCESSING,
        privacy=privacy,
        chunkDuration=chunk_duration,
        sceneDetection=scene_detection,
        sourceVideoKey=object_key,
        sourceVideoUrl=source_video_url,
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
    enqueue_processing(project.id, object_key)
    return project


@router.post("/file", response_model=Project)
async def ingest_uploaded_file(
    file: UploadFile = File(...),
    project_name: str = Form(..., alias="projectName"),
    chunk_duration: int = Form(..., alias="chunkDuration"),
    scene_detection: bool = Form(..., alias="sceneDetection"),
    privacy: PrivacyStatus = Form(...),
) -> Project:
    settings = get_settings()
    storage = StorageService(settings)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")
    _validated_upload_content_type(file)
    object_key = f"uploads/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_slugify(project_name)}-{file.filename}"
    if settings.demo_mode:
        return await _queue_project(
            object_key=object_key,
            project_name=project_name,
            chunk_duration=chunk_duration,
            scene_detection=scene_detection,
            privacy=privacy,
            source_video_url="/demo/short-placeholder.mp4",
        )

    if not storage.ready:
        raise HTTPException(status_code=503, detail="Google Drive storage is not configured for file ingest.")

    with tempfile.TemporaryDirectory(prefix="shortsmith-upload-") as temp_dir:
        temp_path = Path(temp_dir) / (file.filename or "source.mp4")
        content_type = await _persist_upload_to_path(file, temp_path, settings.max_upload_size_bytes)
        drive_file_id = storage.upload_file(temp_path, object_key, content_type)

    return await _queue_project(
        object_key=f"drive:{drive_file_id}",
        project_name=project_name,
        chunk_duration=chunk_duration,
        scene_detection=scene_detection,
        privacy=privacy,
        source_video_url=storage.public_url_for(drive_file_id),
    )


@router.post("/source-url", response_model=Project)
async def ingest_source_url(request: SourceUrlIngestRequest) -> Project:
    settings = get_settings()
    storage = StorageService(settings)
    downloader = SourceDownloader(settings)

    if settings.demo_mode:
        object_key = f"uploads/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_slugify(request.project_name)}-amazon-minitv-demo.mp4"
        return await _queue_project(
            object_key=object_key,
            project_name=request.project_name,
            chunk_duration=request.chunk_duration,
            scene_detection=request.scene_detection,
            privacy=request.privacy,
            source_video_url=request.source_url,
        )

    if not storage.ready:
        raise HTTPException(status_code=503, detail="Google Drive storage is not configured for source URL ingest.")

    try:
        downloader.validate_supported_url(request.source_url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    with tempfile.TemporaryDirectory(prefix="shortsmith-source-") as temp_dir:
        temp_path = Path(temp_dir)
        try:
            downloaded_path = downloader.download(request.source_url, temp_path)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except subprocess.CalledProcessError as error:
            detail = error.stderr.strip() or error.stdout.strip() or "yt-dlp failed to download the source video."
            raise HTTPException(status_code=502, detail=detail) from error

        extension = downloaded_path.suffix or ".mp4"
        object_key = (
            f"uploads/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-"
            f"{_slugify(request.project_name)}-amazon-minitv{extension}"
        )
        content_type = mimetypes.guess_type(downloaded_path.name)[0] or "video/mp4"
        drive_file_id = storage.upload_file(downloaded_path, object_key, content_type)

    return await _queue_project(
        object_key=f"drive:{drive_file_id}",
        project_name=request.project_name,
        chunk_duration=request.chunk_duration,
        scene_detection=request.scene_detection,
        privacy=request.privacy,
        source_video_url=storage.public_url_for(drive_file_id),
    )
