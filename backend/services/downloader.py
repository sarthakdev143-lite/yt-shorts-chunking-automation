from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.core.config import Settings

AMAZON_MINITV_URL_PATTERN = re.compile(r"^https?://(?:www\.)?amazon\.in/minitv/", re.IGNORECASE)


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
                "Set the AMAZON_MINITV_COOKIES environment variable with the "
                "contents of your amazon.in cookies.txt file and redeploy. "
                "See the README for export instructions."
            )

        destination_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(destination_dir / "source.%(ext)s")

        # Write cookies to a temp file so yt-dlp can use them.
        # We use a separate TemporaryDirectory so the cookies file is cleaned
        # up even if the download fails.
        with tempfile.TemporaryDirectory(prefix="shortsmith-cookies-") as cookies_dir:
            cookies_path = Path(cookies_dir) / "cookies.txt"
            cookies_path.write_text(self.settings.amazon_minitv_cookies, encoding="utf-8")

            command = [
                "yt-dlp",
                "--no-playlist",
                "--restrict-filenames",
                "--merge-output-format", "mp4",
                "--cookies", str(cookies_path),
                # Explicitly prefer mp4 so we don't end up with webm on Render
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", output_template,
                source_url,
            ]

            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr.strip()
                # Give a more actionable error for auth failures
                if "404" in stderr or "login" in stderr.lower() or "sign in" in stderr.lower():
                    raise RuntimeError(
                        "Amazon miniTV returned a 404 or auth error. "
                        "Your cookies may have expired — re-export them from your browser "
                        "after logging into amazon.in and update the AMAZON_MINITV_COOKIES "
                        "env var on Render."
                    ) from exc
                raise

        matches = sorted(destination_dir.glob("source.*"))
        video_files = [
            path for path in matches
            if path.suffix.lower() not in {
                ".json", ".part", ".txt", ".vtt", ".srt",
                ".jpg", ".jpeg", ".png", ".webp",
            }
        ]
        if not video_files:
            raise RuntimeError(
                "yt-dlp completed without producing a downloadable video file."
            )
        return video_files[0]