from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from celery import Celery

from backend.api.schemas import Chunk, ChunkStatus, DuplicateCheck, ProjectStatus, ReframeSettings, TimeRange
from backend.core.config import get_settings
from backend.services.processor import VideoProcessor
from backend.services.repository import get_repository
from backend.services.storage import StorageService
from backend.services.transcriber import GroqTranscriber

settings = get_settings()
celery_app = Celery(
    "shortsmith",
    broker=settings.upstash_redis_url or "memory://",
    backend=settings.upstash_redis_url or "cache+memory://",
)
celery_app.conf.task_default_queue = "shortsmith-processing"


@celery_app.task(name="shortsmith.process_project")
def process_project_task(project_id: str, object_key: str) -> dict[str, str]:
    repository = get_repository()
    project = repository.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} was not found")

    if settings.demo_mode or not settings.google_drive_ready:
        project.processing_stage = "Demo mode processing completed"
        project.upload_progress = 100
        project.status = ProjectStatus.READY
        if not project.chunks:
            project.chunks = [
                Chunk(
                    id=f"{project.id}_demo_chunk_01",
                    projectId=project.id,
                    order=1,
                    title=f"{project.name} highlight",
                    description="Generated from the demo processing path.",
                    tags=["demo", "shorts"],
                    status=ChunkStatus.PENDING,
                    durationSeconds=min(project.chunk_duration, 45),
                    sourceRange={"startSeconds": 0, "endSeconds": min(project.chunk_duration, 45)},
                    trimRange={"startSeconds": 0, "endSeconds": min(project.chunk_duration, 45)},
                    reframe=ReframeSettings(zoom=1.12, blur=26),
                    videoUrl="/demo/short-placeholder.mp4",
                    thumbnailUrl="/demo/thumb-01.jpg",
                    r2VideoUrl="https://demo-r2.example.com/generated/demo.mp4",
                    r2ThumbnailUrl="https://demo-r2.example.com/generated/demo.jpg",
                    scheduledFor=None,
                    uploadedAt=None,
                    youtubeVideoId=None,
                    uploadAttempts=0,
                    duplicateCheck=DuplicateCheck(status="clear", matchedTitle=None),
                    lastError=None,
                    subtitleCues=[],
                )
            ]
        repository.save_project(project)
        repository.append_activity(f"Demo processing completed for {project.name}", kind="processing")
        return {"status": "demo-complete"}

    storage = StorageService(settings)
    processor = VideoProcessor(settings)
    transcriber = GroqTranscriber(settings)

    with tempfile.TemporaryDirectory(prefix="shortsmith-") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = storage.download_object(object_key, temp_path / "source.mp4")
        raw_chunk_path = processor.split_fixed_chunk(source_path, temp_path / "chunk-01.mp4", start_seconds=0, duration_seconds=project.chunk_duration)
        reframed_path = processor.reframe_vertical(raw_chunk_path, temp_path / "chunk-01-vertical.mp4", blur=28, zoom=1.14)
        audio_path = processor.extract_audio(reframed_path, temp_path / "chunk-01.mp3")
        subtitle_text = transcriber.transcribe_to_srt(audio_path)
        subtitle_path = temp_path / "chunk-01.srt"
        subtitle_path.write_text(subtitle_text, encoding="utf-8")
        subtitled_path = processor.burn_subtitles(reframed_path, subtitle_path, temp_path / "chunk-01-subtitled.mp4")
        thumbnail_path = processor.extract_thumbnail(subtitled_path, temp_path / "chunk-01.jpg", timestamp=1.0)

        video_key = f"projects/{project.id}/chunks/chunk-01.mp4"
        thumb_key = f"projects/{project.id}/chunks/chunk-01.jpg"
        video_url = storage.upload_file(subtitled_path, video_key, "video/mp4")
        thumbnail_url = storage.upload_file(thumbnail_path, thumb_key, "image/jpeg")
        storage.delete_object(object_key)

        chunk = Chunk(
            id=f"{project.id}_chunk_01",
            projectId=project.id,
            order=1,
            title=f"{project.name} highlight",
            description=project.description_template,
            tags=["shorts", "automation"],
            status=ChunkStatus.PENDING,
            durationSeconds=project.chunk_duration,
            sourceRange=TimeRange(startSeconds=0, endSeconds=project.chunk_duration),
            trimRange=TimeRange(startSeconds=0, endSeconds=project.chunk_duration),
            reframe=ReframeSettings(zoom=1.14, blur=28),
            videoUrl=video_url or "/demo/short-placeholder.mp4",
            thumbnailUrl=thumbnail_url or "/demo/thumb-01.jpg",
            r2VideoUrl=video_url or video_key,
            r2ThumbnailUrl=thumbnail_url or thumb_key,
            scheduledFor=None,
            uploadedAt=None,
            youtubeVideoId=None,
            uploadAttempts=0,
            duplicateCheck=DuplicateCheck(status="clear", matchedTitle=None),
            lastError=None,
            subtitleCues=[],
        )
        project.chunks = [chunk]
        project.status = ProjectStatus.READY
        project.processing_stage = "Chunk 01 processed"
        project.upload_progress = 100
        project.updated_at = datetime.now(timezone.utc).isoformat()
        repository.save_project(project)
        repository.append_activity(f"Chunk processing completed for {project.name}", kind="processing")

    return {"status": "completed"}


def enqueue_processing(project_id: str, object_key: str) -> None:
    if settings.upstash_redis_url:
        process_project_task.delay(project_id, object_key)
        return
    process_project_task(project_id, object_key)
