from __future__ import annotations

import re
import shutil
import subprocess
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
            raise RuntimeError("yt-dlp was not found on PATH. Install yt-dlp on the backend host to enable URL downloads.")

    def download(self, source_url: str, destination_dir: Path) -> Path:
        self.validate_supported_url(source_url)
        self.ensure_yt_dlp()

        destination_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(destination_dir / "source.%(ext)s")
        command = [
            "yt-dlp",
            "--no-playlist",
            "--restrict-filenames",
            "--merge-output-format",
            "mp4",
            "-o",
            output_template,
            source_url,
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)

        matches = sorted(destination_dir.glob("source.*"))
        video_files = [path for path in matches if path.suffix.lower() not in {".json", ".part", ".txt", ".vtt", ".srt", ".jpg", ".jpeg", ".png", ".webp"}]
        if not video_files:
            raise RuntimeError("yt-dlp completed without producing a downloadable video file.")
        return video_files[0]
