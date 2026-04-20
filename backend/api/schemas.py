from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ChunkStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SKIPPED = "skipped"
    UPLOADED = "uploaded"


class ProjectStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    SCHEDULED = "scheduled"
    COMPLETE = "complete"
    FAILED = "failed"


class PrivacyStatus(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class ScheduleMode(StrEnum):
    MANUAL = "manual"
    INTERVAL = "interval"


class ActivityKind(StrEnum):
    PROCESSING = "processing"
    UPLOAD = "upload"
    STORAGE = "storage"


class ServiceStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    DEMO = "demo"


class SubtitleCue(BaseModel):
    id: str
    start_seconds: float = Field(alias="startSeconds")
    end_seconds: float = Field(alias="endSeconds")
    text: str

    model_config = {"populate_by_name": True}


class DuplicateCheck(BaseModel):
    status: str
    matched_title: str | None = Field(alias="matchedTitle")

    model_config = {"populate_by_name": True}


class TimeRange(BaseModel):
    start_seconds: float = Field(alias="startSeconds")
    end_seconds: float = Field(alias="endSeconds")

    model_config = {"populate_by_name": True}


class ReframeSettings(BaseModel):
    zoom: float
    blur: int


class Chunk(BaseModel):
    id: str
    project_id: str = Field(alias="projectId")
    order: int
    title: str
    description: str
    tags: list[str]
    status: ChunkStatus
    duration_seconds: int = Field(alias="durationSeconds")
    source_range: TimeRange = Field(alias="sourceRange")
    trim_range: TimeRange = Field(alias="trimRange")
    reframe: ReframeSettings
    video_url: str = Field(alias="videoUrl")
    thumbnail_url: str = Field(alias="thumbnailUrl")
    r2_video_url: str = Field(alias="r2VideoUrl")
    r2_thumbnail_url: str = Field(alias="r2ThumbnailUrl")
    scheduled_for: str | None = Field(alias="scheduledFor")
    uploaded_at: str | None = Field(alias="uploadedAt")
    youtube_video_id: str | None = Field(alias="youtubeVideoId")
    upload_attempts: int = Field(alias="uploadAttempts")
    duplicate_check: DuplicateCheck = Field(alias="duplicateCheck")
    last_error: str | None = Field(alias="lastError")
    subtitle_cues: list[SubtitleCue] = Field(alias="subtitleCues")

    model_config = {"populate_by_name": True}


class Project(BaseModel):
    id: str
    name: str
    status: ProjectStatus
    privacy: PrivacyStatus
    chunk_duration: int = Field(alias="chunkDuration")
    scene_detection: bool = Field(alias="sceneDetection")
    source_video_key: str = Field(alias="sourceVideoKey")
    source_video_url: str = Field(alias="sourceVideoUrl")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    upload_progress: int = Field(alias="uploadProgress")
    processing_stage: str = Field(alias="processingStage")
    queue_depth: int = Field(alias="queueDepth")
    channel_name: str = Field(alias="channelName")
    schedule_mode: ScheduleMode = Field(alias="scheduleMode")
    daily_interval_hours: int | None = Field(alias="dailyIntervalHours")
    description_template: str = Field(alias="descriptionTemplate")
    chunks: list[Chunk]

    model_config = {"populate_by_name": True}


class ActivityItem(BaseModel):
    id: str
    timestamp: str
    label: str
    kind: ActivityKind


class DashboardSummary(BaseModel):
    total_projects: int = Field(alias="totalProjects")
    approved_chunks: int = Field(alias="approvedChunks")
    pending_chunks: int = Field(alias="pendingChunks")
    uploaded_chunks: int = Field(alias="uploadedChunks")
    active_processing_jobs: int = Field(alias="activeProcessingJobs")

    model_config = {"populate_by_name": True}


class ProjectOverviewResponse(BaseModel):
    projects: list[Project]
    activity: list[ActivityItem]
    summary: DashboardSummary


class ServiceHealth(BaseModel):
    name: str
    status: ServiceStatus
    detail: str


class PlatformHealthResponse(BaseModel):
    mode: str
    backend_url: str | None = Field(alias="backendUrl")
    services: list[ServiceHealth]

    model_config = {"populate_by_name": True}


class SettingsResponse(BaseModel):
    auth: dict[str, Any]
    storage: dict[str, Any]
    processing: dict[str, Any]
    data: dict[str, Any]


class SourceUrlIngestRequest(BaseModel):
    source_url: str = Field(alias="sourceUrl")
    project_name: str = Field(alias="projectName")
    chunk_duration: int = Field(alias="chunkDuration")
    scene_detection: bool = Field(alias="sceneDetection")
    privacy: PrivacyStatus

    model_config = {"populate_by_name": True}


class CreateProjectRequest(BaseModel):
    name: str
    chunk_duration: int = Field(alias="chunkDuration")
    scene_detection: bool = Field(alias="sceneDetection")
    privacy: PrivacyStatus

    model_config = {"populate_by_name": True}


class ChunkMetadataUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    status: ChunkStatus | None = None


class ChunkSubtitleUpdateRequest(BaseModel):
    subtitle_cues: list[SubtitleCue] = Field(alias="subtitleCues")

    model_config = {"populate_by_name": True}


class ChunkReframeRequest(BaseModel):
    blur: int
    zoom: float


class ChunkTrimRequest(BaseModel):
    start_seconds: float = Field(alias="startSeconds")
    end_seconds: float = Field(alias="endSeconds")

    model_config = {"populate_by_name": True}


class ChunkReorderRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    ordered_chunk_ids: list[str] = Field(alias="orderedChunkIds")

    model_config = {"populate_by_name": True}


class YouTubeDuplicateCheckRequest(BaseModel):
    access_token: str = Field(alias="accessToken")
    title: str

    model_config = {"populate_by_name": True}


class YouTubeUploadRequest(BaseModel):
    access_token: str = Field(alias="accessToken")
    refresh_token: str | None = Field(default=None, alias="refreshToken")
    chunk_id: str = Field(alias="chunkId")
    privacy_status: PrivacyStatus = Field(alias="privacyStatus")

    model_config = {"populate_by_name": True}


class EventPayload(BaseModel):
    project_id: str = Field(alias="projectId")
    message: str
    kind: str
    timestamp: datetime

    model_config = {"populate_by_name": True}
