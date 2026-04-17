**Build a Video Chunker & YouTube Shorts Uploader — Full Stack Web App**

Build a production-grade full stack web application that takes a long-form video (owned/licensed), splits it into chunks, reformats each for YouTube Shorts (9:16), lets the user preview & review each chunk in the browser, and uploads approved ones to YouTube. Everything must use free tiers only.

---

**Stack**

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, shadcn/ui |
| Backend API | FastAPI (Python) hosted on **Render** free tier |
| Video Processing | FFmpeg via subprocess |
| Transcription | **Groq Whisper API** (free tier) |
| Job Queue | **Upstash Redis** (free tier) + Celery |
| File Storage | **Cloudflare R2** (free tier, 10GB, zero egress) |
| Database | **Supabase** PostgreSQL (free tier) |
| Auth | NextAuth.js (Google OAuth) |
| Frontend Hosting | **Vercel** (free tier) |
| YouTube Upload | YouTube Data API v3 (free, OAuth 2.0) |

---

**Storage Strategy (to stay within free limits)**
- Upload raw video chunk to R2 → process it → store only the final processed Short on R2
- Delete the raw chunk immediately after processing
- After successful YouTube upload → delete the processed Short from R2 too
- R2 acts as a **temporary transit layer only**, not permanent storage
- This keeps usage well under 2GB at any time regardless of source video size

---

**1. Upload & Project Setup (Page 1)**
- Drag & drop or file picker to upload a video directly to Cloudflare R2 (via presigned URL, bypassing the Render backend to avoid memory limits)
- User sets: project name, chunk duration, scene detection on/off, default privacy status
- Upload progress bar shown in UI
- On completion, a Celery job is triggered via Upstash Redis to begin async processing

---

**2. Processing Pipeline (Background — Render + Celery)**
For each chunk the backend:
- Downloads the source video from R2
- Splits at scene-aware or fixed intervals using FFmpeg
- Reformats each chunk to **1080x1920** with a blurred zoomed background fill (FFmpeg)
- Sends audio to **Groq Whisper API** for transcription, receives .srt subtitles
- Burns subtitles onto the video (FFmpeg)
- Extracts the most visually distinct frame as thumbnail
- Uploads processed chunk + thumbnail to R2
- Deletes raw source chunk from R2
- Saves chunk metadata (R2 URLs, status, title, description, tags) to Supabase
- Emits real-time status updates to frontend via **Server-Sent Events (SSE)**

---

**3. Review Dashboard (Page 2 — core of the app)**
Card-based dashboard, one card per chunk, each containing:
- **Inline video player** streaming directly from R2 (zero egress cost)
- **Subtitle editor** — editable text synced to video timestamps, reburns on save
- **Metadata editor** — editable title, description, tags per chunk
- **Thumbnail picker** — auto-selected or scrub the timeline to pick a custom frame
- **Reframe controls** — adjust blur intensity and zoom level, reprocess with one click
- **Trim controls** — set new start/end timestamps, reprocess with one click
- Per-chunk status badge: Pending / Approved / Skipped / Uploaded
- Bulk actions: Approve All, Skip All

---

**4. Upload Scheduler (Page 3)**
- Drag to reorder chunks (sets upload sequence)
- Options: Upload Now / Schedule (set date & time per chunk or a daily interval)
- Live upload queue showing: Queued → Uploading → Done
- **Duplicate guard** — checks YouTube channel before each upload to avoid re-uploads
- **Resume support** — if upload fails mid-way, retries from that exact chunk
- After each successful YouTube upload, the chunk is automatically deleted from R2

---

**5. Auth**
- Google OAuth via NextAuth.js
- Same Google account is reused for YouTube Data API access (no second login)
- OAuth tokens stored in Supabase, auto-refreshed
- Scoped only to YouTube upload permissions

---

**6. UI Design Direction**
- Dark mode first
- Clean minimal dashboard aesthetic (inspired by Linear / Vercel UI)
- Sidebar navigation: Projects / Review / Scheduler / Settings
- Real-time job progress via Server-Sent Events (SSE) — no polling
- Fully responsive
- shadcn/ui components throughout for consistency

---

**7. Render Free Tier Handling**
- Backend sleeps after 15 minutes of inactivity — show a "Waking up server..." indicator on the frontend when the first request is slow
- Keep FFmpeg processing within 512MB RAM by processing one chunk at a time, never in parallel
- All heavy file I/O goes through R2 presigned URLs directly — never through Render's memory

---

**8. Folder Structure**

```
/frontend (Next.js — deployed on Vercel)
  /app
    /dashboard
    /review/[projectId]
    /scheduler/[projectId]
    /settings
  /components
  /lib
    /supabase.ts
    /r2.ts
    /youtube.ts

/backend (FastAPI — deployed on Render)
  /api
    /routes
      upload.py
      projects.py
      chunks.py
      youtube.py
  /workers
    tasks.py        → Celery tasks
  /services
    processor.py    → FFmpeg splitting, framing, subtitle burn
    transcriber.py  → Groq Whisper API calls
    uploader.py     → YouTube Data API logic
    storage.py      → Cloudflare R2 (boto3 S3-compatible)
  /models
    db.py           → Supabase / SQLAlchemy models
  main.py

docker-compose.yml  → local dev: FastAPI + Upstash Redis emulator + Supabase local
.env.example        → all required environment variables listed
README.md           → full setup instructions
```

---

**Environment Variables Needed**
```
GROQ_API_KEY
CLOUDFLARE_R2_ACCESS_KEY
CLOUDFLARE_R2_SECRET_KEY
CLOUDFLARE_R2_BUCKET_NAME
CLOUDFLARE_R2_ENDPOINT
SUPABASE_URL
SUPABASE_ANON_KEY
UPSTASH_REDIS_URL
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
NEXTAUTH_SECRET
```

---

**Important:** This tool is intended strictly for videos the user owns or has explicit rights to redistribute. No third-party content sources should be assumed or hardcoded.
