from __future__ import annotations

import json
import subprocess
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

# Render's Redis connectionString uses redis:// but requires TLS (rediss://).
# The CELERY_BROKER_USE_SSL env var signals we should upgrade the scheme.
_broker_url = settings.upstash_redis_url or "memory://"
_use_ssl = False
if (
    _broker_url.startswith("redis://")
    and "localhost" not in _broker_url
    and "127.0.0.1" not in _broker_url
):
    _broker_url = _broker_url.replace("redis://", "rediss://", 1)
    _use_ssl = True

celery_app = Celery(
    "shortsmith",
    broker=_broker_url,
    backend=_broker_url,
)
celery_app.conf.task_default_queue = "shortsmith-processing"

if _use_ssl:
    _ssl_opts = {"ssl_cert_reqs": None}
    celery_app.conf.broker_use_ssl = _ssl_opts
    celery_app.conf.redis_backend_use_ssl = _ssl_opts


def _probe_duration(path: Path, ffprobe_binary: str) -> float:
    """Return the total duration of a video file in seconds using ffprobe."""
    result = subprocess.run(
        [
            ffprobe_binary,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


@celery_app.task(name="shortsmith.process_project")
def process_project_task(project_id: str, object_key: str) -> dict[str, str]:
    repository = get_repository()
    project = repository.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} was not found")

    # ------------------------------------------------------------------ #
    # Demo / unconfigured path                                            #
    # ------------------------------------------------------------------ #
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
                    sourceRange=TimeRange(
                        startSeconds=0,
                        endSeconds=min(project.chunk_duration, 45),
                    ),
                    trimRange=TimeRange(
                        startSeconds=0,
                        endSeconds=min(project.chunk_duration, 45),
                    ),
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
        repository.append_activity(
            f"Demo processing completed for {project.name}", kind="processing"
        )
        return {"status": "demo-complete"}

    # ------------------------------------------------------------------ #
    # Live path                                                           #
    # ------------------------------------------------------------------ #
    storage = StorageService(settings)
    processor = VideoProcessor(settings)
    transcriber = GroqTranscriber(settings)

    with tempfile.TemporaryDirectory(prefix="shortsmith-") as temp_dir:
        temp_path = Path(temp_dir)

        # 1. Download source from Google Drive
        source_path = storage.download_object(object_key, temp_path / "source.mp4")

        # 2. Probe total duration so we can build all chunks
        total_duration = _probe_duration(source_path, settings.ffprobe_binary)
        chunk_duration = project.chunk_duration
        num_chunks = max(1, int(total_duration // chunk_duration))

        chunks: list[Chunk] = []

        for index in range(num_chunks):
            chunk_num = index + 1
            start_seconds = index * chunk_duration
            # Last chunk gets whatever is left (may be shorter)
            actual_duration = min(chunk_duration, total_duration - start_seconds)

            project.processing_stage = f"Processing chunk {chunk_num} of {num_chunks}"
            project.upload_progress = int((index / num_chunks) * 90)
            repository.save_project(project)

            chunk_id = f"{project.id}_chunk_{chunk_num:02d}"
            raw_chunk = processor.split_fixed_chunk(
                source_path,
                temp_path / f"chunk-{chunk_num:02d}-raw.mp4",
                start_seconds=start_seconds,
                duration_seconds=int(actual_duration),
            )
            reframed = processor.reframe_vertical(
                raw_chunk,
                temp_path / f"chunk-{chunk_num:02d}-vertical.mp4",
                blur=28,
                zoom=1.14,
            )

            # Transcription (skip gracefully if Groq key absent)
            subtitled = reframed
            if transcriber.ready:
                audio_path = processor.extract_audio(
                    reframed, temp_path / f"chunk-{chunk_num:02d}.mp3"
                )
                subtitle_text = transcriber.transcribe_to_srt(audio_path)
                subtitle_path = temp_path / f"chunk-{chunk_num:02d}.srt"
                subtitle_path.write_text(subtitle_text, encoding="utf-8")
                subtitled = processor.burn_subtitles(
                    reframed,
                    subtitle_path,
                    temp_path / f"chunk-{chunk_num:02d}-subtitled.mp4",
                )

            thumbnail = processor.extract_thumbnail(
                subtitled, temp_path / f"chunk-{chunk_num:02d}.jpg", timestamp=1.0
            )

            # Upload processed assets to Drive
            video_key = f"projects/{project.id}/chunks/chunk-{chunk_num:02d}.mp4"
            thumb_key = f"projects/{project.id}/chunks/chunk-{chunk_num:02d}.jpg"
            video_file_id = storage.upload_file(subtitled, video_key, "video/mp4")
            thumb_file_id = storage.upload_file(thumbnail, thumb_key, "image/jpeg")

            # Convert file IDs to public URLs
            video_url = storage.public_url_for(video_file_id)
            thumbnail_url = storage.public_url_for(thumb_file_id)

            chunks.append(
                Chunk(
                    id=chunk_id,
                    projectId=project.id,
                    order=chunk_num,
                    title=f"{project.name} — part {chunk_num}",
                    description=project.description_template,
                    tags=["shorts", "automation"],
                    status=ChunkStatus.PENDING,
                    durationSeconds=int(actual_duration),
                    sourceRange=TimeRange(
                        startSeconds=start_seconds,
                        endSeconds=start_seconds + actual_duration,
                    ),
                    trimRange=TimeRange(
                        startSeconds=start_seconds,
                        endSeconds=start_seconds + actual_duration,
                    ),
                    reframe=ReframeSettings(zoom=1.14, blur=28),
                    videoUrl=video_url,
                    thumbnailUrl=thumbnail_url,
                    r2VideoUrl=video_url,
                    r2ThumbnailUrl=thumbnail_url,
                    scheduledFor=None,
                    uploadedAt=None,
                    youtubeVideoId=None,
                    uploadAttempts=0,
                    duplicateCheck=DuplicateCheck(status="clear", matchedTitle=None),
                    lastError=None,
                    subtitleCues=[],
                )
            )

            # Clean up per-chunk temp files to stay inside Render's disk limit
            raw_chunk.unlink(missing_ok=True)
            reframed.unlink(missing_ok=True)
            subtitled.unlink(missing_ok=True)
            thumbnail.unlink(missing_ok=True)

        # 3. Delete the source from Drive now that all chunks are processed
        storage.delete_object(object_key)

        # 4. Persist final project state
        project.chunks = chunks
        project.status = ProjectStatus.READY
        project.processing_stage = f"All {num_chunks} chunks processed"
        project.upload_progress = 100
        project.updated_at = datetime.now(timezone.utc).isoformat()
        repository.save_project(project)
        repository.append_activity(
            f"Chunk processing completed for {project.name} ({num_chunks} chunks)",
            kind="processing",
        )

    return {"status": "completed", "chunks": num_chunks}


def enqueue_processing(project_id: str, object_key: str) -> None:
    if settings.upstash_redis_url:
        process_project_task.delay(project_id, object_key)
        return
    process_project_task(project_id, object_key)