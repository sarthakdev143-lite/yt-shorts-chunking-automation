from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from backend.core.config import Settings


class VideoProcessor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ensure_ffmpeg(self) -> None:
        if shutil.which(self.settings.ffmpeg_binary) is None:
            raise RuntimeError("ffmpeg binary was not found on PATH.")

    def run(self, *args: str) -> None:
        subprocess.run([self.settings.ffmpeg_binary, *args], check=True, capture_output=True)

    def split_fixed_chunk(self, source: Path, destination: Path, start_seconds: float, duration_seconds: int) -> Path:
        self.ensure_ffmpeg()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.run("-y", "-ss", str(start_seconds), "-i", str(source), "-t", str(duration_seconds), "-c:v", "libx264", "-c:a", "aac", str(destination))
        return destination

    def reframe_vertical(self, source: Path, destination: Path, *, blur: int, zoom: float) -> Path:
        self.ensure_ffmpeg()
        destination.parent.mkdir(parents=True, exist_ok=True)
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"boxblur={blur}:1[bg];"
            f"[0:v]scale=iw*{zoom}:ih*{zoom}:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        self.run("-y", "-i", str(source), "-filter_complex", filter_complex, "-c:v", "libx264", "-c:a", "aac", str(destination))
        return destination

    def burn_subtitles(self, source: Path, subtitle_path: Path, destination: Path) -> Path:
        self.ensure_ffmpeg()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.run("-y", "-i", str(source), "-vf", f"subtitles={subtitle_path.as_posix()}", "-c:v", "libx264", "-c:a", "aac", str(destination))
        return destination

    def extract_audio(self, source: Path, destination: Path) -> Path:
        self.ensure_ffmpeg()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.run("-y", "-i", str(source), "-vn", "-acodec", "mp3", str(destination))
        return destination

    def extract_thumbnail(self, source: Path, destination: Path, *, timestamp: float = 1.0) -> Path:
        self.ensure_ffmpeg()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.run("-y", "-ss", str(timestamp), "-i", str(source), "-frames:v", "1", str(destination))
        return destination
