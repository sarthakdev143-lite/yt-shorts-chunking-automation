from __future__ import annotations

import base64
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.core.config import Settings

AMAZON_MINITV_URL_PATTERN = re.compile(r"^https?://(?:www\.)?amazon\.in/minitv/", re.IGNORECASE)


def _resolve_cookies_content(raw: str) -> str:
    """
    Render (and other platforms) encode newlines as literal \\n when you paste
    multi-line text into their env var UI.  This function handles three cases:

    1. Properly encoded base64 string  ->  decode and return
    2. Raw cookies.txt with literal \\n  ->  replace with real newlines
    3. Raw cookies.txt with real newlines  ->  return as-is
    """
    stripped = raw.strip()

    # Case 1: base64-encoded cookies (recommended for Render)
    # Heuristic: no real newlines, only base64 chars, long enough to be a file
    if "\n" not in stripped and len(stripped) > 80:
        try:
            decoded = base64.b64decode(stripped).decode("utf-8")
            if "amazon" in decoded.lower() or "# Netscape" in decoded:
                return decoded
        except Exception:
            pass

    # Case 2 & 3: replace escaped newlines then return
    return stripped.replace("\\n", "\n")


class SourceDownloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_supported_url(self, source_url: str) -> None:
        if not AMAZON_MINITV_URL_PATTERN.match(source_url):
            raise ValueError("Only Amazon miniTV URLs from amazon.in/minitv are supported.")

    def ensure_yt_dlp(self) -> None:
        if shutil.which("yt-dlp") is None:
            raise RuntimeError(
                "yt-dlp was not found on PATH. "
                "Install yt-dlp on the backend host to enable URL downloads."
            )

    def download(self, source_url: str, destination_dir: Path) -> Path:
        self.validate_supported_url(source_url)
        self.ensure_yt_dlp()

        if not self.settings.amazon_minitv_ready:
            raise RuntimeError(
                "Amazon miniTV downloads require authentication cookies. "
                "Set AMAZON_MINITV_COOKIES on Render using the base64 method."
            )

        destination_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(destination_dir / "source.%(ext)s")

        cookies_content = _resolve_cookies_content(self.settings.amazon_minitv_cookies)

        with tempfile.TemporaryDirectory(prefix="shortsmith-cookies-") as cookies_dir:
            cookies_path = Path(cookies_dir) / "cookies.txt"
            cookies_path.write_text(cookies_content, encoding="utf-8")

            command = [
                "yt-dlp",
                "--no-playlist",
                "--restrict-filenames",
                "--merge-output-format", "mp4",
                "--cookies", str(cookies_path),
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", output_template,
                source_url,
            ]

            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr.strip()
                stdout = exc.stdout.strip()
                detail = stderr or stdout or "yt-dlp exited with a non-zero status."
                raise RuntimeError(
                    f"yt-dlp failed to download the Amazon miniTV source.\n\nRaw error:\n{detail}"
                ) from exc

        matches = sorted(destination_dir.glob("source.*"))
        video_files = [
            path for path in matches
            if path.suffix.lower() not in {
                ".json", ".part", ".txt", ".vtt", ".srt",
                ".jpg", ".jpeg", ".png", ".webp",
            }
        ]
        if not video_files:
            raise RuntimeError("yt-dlp completed without producing a downloadable video file.")
        return video_files[0]