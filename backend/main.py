from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.chunks import router as chunks_router
from backend.api.routes.projects import router as projects_router
from backend.api.routes.upload import router as upload_router
from backend.api.routes.youtube import router as youtube_router
from backend.core.config import get_settings
from backend.models.db import init_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.database_url and not settings.demo_mode:
        init_database(settings.database_url)
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
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


@app.get("/health")
def health() -> dict:
    return {
        "mode": "demo" if settings.demo_mode else "live",
        "backendUrl": None,
        "services": [
            {"name": "Render API", "status": "demo" if settings.demo_mode else "ready", "detail": "FastAPI server is responding."},
            {"name": "Cloudflare R2", "status": "ready" if settings.r2_ready else "demo", "detail": "Temporary transit bucket is configured." if settings.r2_ready else "R2 env vars are missing."},
            {"name": "Upstash Redis", "status": "ready" if settings.upstash_redis_url else "demo", "detail": "Celery broker is configured." if settings.upstash_redis_url else "Memory broker fallback is active."},
            {"name": "Supabase", "status": "ready" if settings.database_url else "demo", "detail": "SQLAlchemy persistence is configured." if settings.database_url else "Using the bundled demo seed."},
            {"name": "YouTube OAuth", "status": "ready" if settings.youtube_ready else "demo", "detail": "Google OAuth credentials are configured." if settings.youtube_ready else "OAuth env vars are missing."},
        ],
    }


@app.get("/health/settings")
def settings_snapshot() -> dict:
    return {
        "auth": {
            "googleConfigured": settings.youtube_ready,
            "nextAuthSecretConfigured": bool(settings.nextauth_secret),
            "youtubeScope": "openid email profile https://www.googleapis.com/auth/youtube.upload",
        },
        "storage": {
            "r2Configured": settings.r2_ready,
            "bucketName": settings.cloudflare_r2_bucket_name,
            "tempRetentionRule": "Delete raw chunk after processing and delete final Short after successful YouTube upload.",
        },
        "processing": {
            "groqConfigured": bool(settings.groq_api_key),
            "chunkConcurrency": 1,
            "ffmpegStrategy": "Fixed or scene-aware chunking processed serially to stay within free-tier RAM.",
        },
        "data": {
            "supabaseConfigured": bool(settings.database_url or settings.supabase_url),
            "redisConfigured": bool(settings.upstash_redis_url),
        },
    }
