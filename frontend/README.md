# Shortsmith

Shortsmith is a full stack workflow for turning owned or licensed long-form video into YouTube Shorts.

It is designed around free-tier constraints:
- Direct upload to Cloudflare R2 with presigned URLs so Render never buffers the source file
- Serial FFmpeg processing so chunking stays inside a small memory envelope
- Groq Whisper transcription for subtitles
- Temporary R2 storage only: raw chunks are deleted after processing, and final Shorts are deleted after successful YouTube upload
- Review and scheduling surfaces in a Next.js operator UI

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16 App Router, Tailwind CSS 4, custom shadcn-style component patterns |
| Auth | NextAuth.js with Google OAuth scaffolding |
| Backend API | FastAPI |
| Queue | Celery + Redis / Upstash-compatible broker |
| Processing | FFmpeg via subprocess |
| Transcription | Groq audio transcription API |
| Storage | Cloudflare R2 (S3-compatible) |
| Database | SQLAlchemy against Supabase/Postgres-compatible storage |
| Upload | YouTube Data API v3 scaffolding |

## What is implemented

### Frontend
- Marketing landing page at `/`
- Workspace shell with sidebar navigation
- Dashboard at `/dashboard`
  - Direct upload form with project settings
  - Progress indicator and Render-safe upload explanation
  - Project overview cards and activity stream
- Review dashboard at `/review/[projectId]`
  - Inline video preview
  - Subtitle cue editing with timestamps
  - Per-chunk metadata editing
  - Thumbnail selection
  - Reframe blur/zoom controls
  - Trim controls
  - Approve/skip bulk actions
- Scheduler at `/scheduler/[projectId]`
  - Drag-and-drop ordering
  - Per-chunk scheduling slots
  - Interval scheduling helper
  - Duplicate-guard visibility
  - Upload queue states
- Settings at `/settings`
  - Env readiness surface for OAuth, R2, Groq, Redis, and data persistence
- Health route at `/api/health`
- NextAuth route handler at `/api/auth/[...nextauth]`

### Backend
- FastAPI app in `backend/`
- Upload endpoints for presigning and queue completion
- Project and chunk endpoints
- SSE project event stream endpoint
- Celery worker entrypoint
- Storage, processing, transcription, and YouTube uploader services
- SQLAlchemy models for persisted JSON project payloads and OAuth tokens
- Demo repository seeded from `data/demo-projects.json`

## Project structure

```text
app/
components/
lib/
public/demo/
backend/
  api/routes/
  core/
  models/
  services/
  workers/
data/demo-projects.json
docker-compose.yml
.env.example
```

## Demo mode vs live mode

The repo ships with a seeded demo mode so the UI works without external credentials.

### Demo mode
- `NEXT_PUBLIC_DEMO_MODE=true`
- `DEMO_MODE=true`
- Uses `data/demo-projects.json`
- Frontend upload flow simulates R2 progress
- Backend processing path produces demo chunks if no live storage is configured

### Live mode
Set:
- `NEXT_PUBLIC_DEMO_MODE=false`
- `DEMO_MODE=false`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` or your deployed backend URL
- Valid R2, Groq, Redis, Google OAuth, and Postgres env vars

## Environment variables

Copy `.env.example` to `.env` and fill in the values you actually use.

Core variables:
- `GROQ_API_KEY`
- `CLOUDFLARE_R2_ACCESS_KEY`
- `CLOUDFLARE_R2_SECRET_KEY`
- `CLOUDFLARE_R2_BUCKET_NAME`
- `CLOUDFLARE_R2_ENDPOINT`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `UPSTASH_REDIS_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NEXTAUTH_SECRET`

Additional practical variables for local execution:
- `DATABASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_DEMO_MODE`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `CLOUDFLARE_R2_PUBLIC_BASE_URL`

## Local development

### Frontend only
```bash
npm install
npm run dev
```

### Backend only
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### Worker
```bash
celery -A backend.workers.tasks worker --loglevel=info
```

### Docker Compose
```bash
docker compose up --build
```

The compose stack uses local Postgres and Redis primitives that are compatible with the Supabase/Postgres and Upstash/Redis integration points in the code.

## Backend endpoints

### Upload
- `POST /api/upload/presign`
- `POST /api/upload/complete`

### Projects
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `GET /api/projects/{project_id}/events`

### Chunks
- `PATCH /api/chunks/{chunk_id}/metadata`
- `PATCH /api/chunks/{chunk_id}/subtitles`
- `POST /api/chunks/{chunk_id}/reframe`
- `POST /api/chunks/{chunk_id}/trim`
- `POST /api/chunks/reorder`
- `POST /api/chunks/{chunk_id}/upload`

### YouTube
- `POST /api/youtube/duplicate-check`
- `POST /api/youtube/upload`

## Notes on the live pipeline

The repository includes the service boundaries and orchestration for the production pipeline, but external providers still require real credentials and infrastructure:
- Groq transcription calls the live API only when `GROQ_API_KEY` is present
- R2 presigned uploads require S3-compatible credentials and bucket configuration
- Celery fan-out uses Redis when `UPSTASH_REDIS_URL` is set; otherwise it falls back to an in-process memory broker for local/demo flows
- SQLAlchemy persistence requires `DATABASE_URL`
- YouTube upload scaffolding covers duplicate checks and the resumable upload path; worker-managed artifact handoff remains the intended place to complete channel publication in a fully live deployment

## Verification

Recommended checks:
```bash
npm run lint
npm run build
python -m compileall backend
```

## Compliance

This project is intended only for content that the operator owns or is explicitly licensed to redistribute. No third-party source acquisition is built into the workflow.
