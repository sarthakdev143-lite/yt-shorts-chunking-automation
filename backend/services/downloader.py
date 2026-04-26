from __future__ import annotations

import base64
import http.cookiejar
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

from backend.core.config import Settings

AMAZON_MINITV_URL_PATTERN = re.compile(r"^https?://(?:www\.)?amazon\.in/minitv/", re.IGNORECASE)
AMAZON_MINITV_CONTENT_ID_PATTERN = re.compile(
    r"(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)
AMAZON_MINITV_PAGE_API = "https://www.amazon.in/minitv-pr/api/web/page/title"
AMAZON_MINITV_PAGE_HEADERS = {
    "accounttype": "NEW_GUEST_ACCOUNT",
    "currentpageurl": "/",
    "currentplatform": "dWeb",
}
AMAZON_MINITV_CLIENT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    )
}


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


def _load_cookie_map(raw: str) -> dict[str, str]:
    cookies_content = _resolve_cookies_content(raw)
    with tempfile.TemporaryDirectory(prefix="shortsmith-amazon-cookies-") as cookies_dir:
        cookies_path = Path(cookies_dir) / "cookies.txt"
        cookies_path.write_text(cookies_content, encoding="utf-8")

        cookie_jar = http.cookiejar.MozillaCookieJar(str(cookies_path))
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        return {
            cookie.name: cookie.value
            for cookie in cookie_jar
            if "amazon.in" in cookie.domain.lstrip(".")
        }


class SourceDownloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_supported_url(self, source_url: str) -> None:
        if not AMAZON_MINITV_URL_PATTERN.match(source_url):
            raise ValueError("Only Amazon miniTV URLs from amazon.in/minitv are supported.")

    def _extract_content_id(self, source_url: str) -> str:
        match = AMAZON_MINITV_CONTENT_ID_PATTERN.search(source_url)
        if not match:
            raise RuntimeError("Could not extract the Amazon miniTV content ID from the provided URL.")
        return match.group("id").lower()

    def ensure_yt_dlp(self) -> None:
        if shutil.which("yt-dlp") is None:
            raise RuntimeError(
                "yt-dlp was not found on PATH. "
                "Install yt-dlp on the backend host to enable URL downloads."
            )

    def _build_amazon_client(self, cookies: dict[str, str] | None = None) -> httpx.Client:
        client = httpx.Client(
            follow_redirects=True,
            headers=AMAZON_MINITV_CLIENT_HEADERS,
            timeout=30,
        )
        if cookies:
            client.cookies.update(cookies)
        return client

    def _fetch_playback_payload(self, source_url: str, cookies: dict[str, str] | None = None) -> dict:
        import time
        content_id = self._extract_content_id(source_url)
        asin = f"amzn1.dv.gti.{content_id}"

        with self._build_amazon_client(cookies) as client:
            # Retry the bootstrap page — Amazon miniTV occasionally returns 503
            # for a few seconds before recovering.
            for attempt in range(3):
                bootstrap_response = client.get("https://www.amazon.in/minitv")
                if bootstrap_response.status_code != 503:
                    break
                if attempt < 2:
                    import time
                    time.sleep(2 ** attempt)
            bootstrap_response.raise_for_status()

            for attempt in range(3):
                response = client.get(
                    AMAZON_MINITV_PAGE_API,
                    params={"contentId": asin},
                    headers=AMAZON_MINITV_PAGE_HEADERS,
                )
                if response.status_code != 503:
                    break
                if attempt < 2:
                    time.sleep(2 ** attempt)

            response.raise_for_status()
            payload = response.json()

        network_error = payload.get("networkError") or {}
        status_code = network_error.get("statusCode")
        if status_code:
            error_msg = network_error.get("result", {}).get("errorMsg") or "Amazon miniTV API request failed."
            raise RuntimeError(f"Amazon miniTV page API returned {status_code}: {error_msg}")

        return payload

    @staticmethod
    def _resolve_manifest_url(payload: dict) -> str:
        widgets = payload.get("widgets") or []
        player_widget = next((widget for widget in widgets if widget.get("type") == "PLAYER"), None)
        if not player_widget:
            raise RuntimeError("Amazon miniTV playback data did not include a player widget.")

        playback_assets = player_widget.get("data", {}).get("playbackAssets", {})
        manifest_data = playback_assets.get("manifestData") or []

        for codec in ("H_264", "AVC", "VP9"):
            manifest_url = next(
                (
                    item.get("manifestURL")
                    for item in manifest_data
                    if item.get("codec") == codec and item.get("manifestURL")
                ),
                None,
            )
            if manifest_url:
                return manifest_url

        for item in manifest_data:
            manifest_url = item.get("manifestURL")
            if manifest_url:
                return manifest_url

        manifest_url = playback_assets.get("manifestURL")
        if manifest_url:
            return manifest_url

        raise RuntimeError("Amazon miniTV playback data did not include a downloadable manifest URL.")

    def download(self, source_url: str, destination_dir: Path) -> Path:
        self.validate_supported_url(source_url)
        self.ensure_yt_dlp()

        auth_cookies: dict[str, str] | None = None
        if self.settings.amazon_minitv_ready:
            try:
                auth_cookies = _load_cookie_map(self.settings.amazon_minitv_cookies)
            except Exception:
                auth_cookies = None

        try:
            payload = self._fetch_playback_payload(source_url)
        except RuntimeError as guest_error:
            if not auth_cookies:
                raise
            try:
                payload = self._fetch_playback_payload(source_url, auth_cookies)
            except RuntimeError:
                raise guest_error

        manifest_url = self._resolve_manifest_url(payload)

        destination_dir.mkdir(parents=True, exist_ok=True)
        output_template = str(destination_dir / "source.%(ext)s")
        command = [
            "yt-dlp",
            "--no-playlist",
            "--restrict-filenames",
            "--referer", "https://www.amazon.in/minitv",
            "--merge-output-format", "mp4",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "-o", output_template,
            manifest_url,
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip()
            stdout = exc.stdout.strip()
            detail = stderr or stdout or "yt-dlp exited with a non-zero status."
            raise RuntimeError(
                f"yt-dlp failed to download the Amazon miniTV source manifest.\n\nRaw error:\n{detail}"
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
