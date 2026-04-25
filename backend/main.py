from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from pathlib import Path
import shutil
import sys
from uuid import uuid4

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.api.routes.chunks import router as chunks_router
from backend.api.routes.projects import router as projects_router
from backend.api.routes.upload import router as upload_router
from backend.api.routes.youtube import router as youtube_router
from backend.core.config import get_settings
from backend.models.db import init_database

logging.basicConfig(level=getattr(logging, get_settings().log_level.upper(), logging.INFO))
logger = logging.getLogger("shortsmith.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.database_url and not settings.demo_mode:
        init_database(settings.database_url)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
if settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(chunks_router, prefix=settings.api_prefix)
app.include_router(youtube_router, prefix=settings.api_prefix)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id, "path": str(request.url.path)})
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "requestId": request_id})

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/health")
def health() -> dict:
    ffmpeg_ready = shutil.which(settings.ffmpeg_binary) is not None
    yt_dlp_ready = shutil.which("yt-dlp") is not None
    readiness = "ready" if settings.demo_mode or settings.live_ready else "degraded"
    return {
        "mode": "demo" if settings.demo_mode else "live",
        "status": readiness,
        "backendUrl": settings.backend_url,
        "issues": settings.readiness_issues,
        "services": [
            {"name": "Render API", "status": "demo" if settings.demo_mode else readiness, "detail": "FastAPI server is responding."},
            {"name": "Google Drive", "status": "ready" if settings.google_drive_ready else "demo", "detail": "Drive folder-backed transient storage is configured." if settings.google_drive_ready else "Drive service-account env vars are missing."},
            {"name": "Upstash Redis", "status": "ready" if settings.upstash_redis_url else "demo", "detail": "Celery broker is configured." if settings.upstash_redis_url else "Memory broker fallback is active."},
            {"name": "Supabase", "status": "ready" if settings.database_url else "demo", "detail": "SQLAlchemy persistence is configured." if settings.database_url else "Using the bundled demo seed."},
            {"name": "YouTube OAuth", "status": "ready" if settings.youtube_ready else "demo", "detail": "Google OAuth credentials are configured." if settings.youtube_ready else "OAuth env vars are missing."},
            {"name": "FFmpeg", "status": "ready" if ffmpeg_ready else "degraded", "detail": f"Using binary '{settings.ffmpeg_binary}'." if ffmpeg_ready else f"Binary '{settings.ffmpeg_binary}' was not found on PATH."},
            {"name": "yt-dlp", "status": "ready" if yt_dlp_ready else "degraded", "detail": "yt-dlp is available for source URL downloads." if yt_dlp_ready else "yt-dlp was not found on PATH."},
        ],
    }


@app.get("/ready")
def ready() -> JSONResponse:
    if settings.demo_mode or settings.live_ready:
        return JSONResponse({"status": "ready", "issues": []}, status_code=200)
    return JSONResponse({"status": "degraded", "issues": settings.readiness_issues}, status_code=503)


@app.get("/health/settings")
def settings_snapshot() -> dict:
    return {
        "auth": {
            "googleConfigured": settings.youtube_ready,
            "nextAuthSecretConfigured": bool(settings.nextauth_secret),
            "youtubeScope": "openid email profile https://www.googleapis.com/auth/youtube.upload",
        },
        "storage": {
            "driveConfigured": settings.google_drive_ready,
            "folderId": settings.google_drive_folder_id,
            "tempRetentionRule": "Delete raw source after processing and delete processed Short after successful YouTube upload.",
        },
        "processing": {
            "groqConfigured": bool(settings.groq_api_key),
            "chunkConcurrency": 1,
            "ffmpegStrategy": "Fixed or scene-aware chunking processed serially to stay within free-tier RAM.",
            "maxUploadSizeMb": settings.max_upload_size_mb,
        },
        "data": {
            "supabaseConfigured": bool(settings.database_url or settings.supabase_url),
            "redisConfigured": bool(settings.upstash_redis_url),
        },
    }
