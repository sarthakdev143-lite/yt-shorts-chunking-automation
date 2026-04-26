from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("backend/.env", ".env"), extra="ignore", case_sensitive=False)

    app_name: str = "Shortsmith API"
    environment: str = "development"
    api_prefix: str = "/api"
    demo_mode: bool = True
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS", "cors_origins"),
    )
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("TRUSTED_HOSTS", "trusted_hosts"),
    )
    data_seed_path: str = str(Path("frontend") / "data" / "demo-projects.json")
    backend_url: str | None = Field(default=None, validation_alias=AliasChoices("BACKEND_URL", "backend_url"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "log_level"))
    max_upload_size_mb: int = Field(default=1024, validation_alias=AliasChoices("MAX_UPLOAD_SIZE_MB", "max_upload_size_mb"))

    database_url: str | None = None
    groq_api_key: str | None = None
    groq_transcription_model: str = "whisper-large-v3-turbo"

    google_drive_service_account_file: str | None = None
    google_drive_service_account_json: str | None = None
    google_drive_folder_id: str | None = None

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    upstash_redis_url: str | None = None

    google_client_id: str | None = None
    google_client_secret: str | None = None
    nextauth_secret: str | None = None

    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    # Amazon miniTV cookies — Netscape/Mozilla format cookies.txt content.
    # Export from your browser after logging into amazon.in, then paste the
    # full file content as this env var value on Render.
    amazon_minitv_cookies: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AMAZON_MINITV_COOKIES", "amazon_minitv_cookies"),
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def parse_trusted_hosts(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_ranges(self) -> "Settings":
        if self.max_upload_size_mb <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be greater than zero.")
        return self

    @property
    def root_path(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_seed_path(self) -> Path:
        return (self.root_path / self.data_seed_path).resolve()

    @property
    def google_drive_ready(self) -> bool:
        return bool((self.google_drive_service_account_file or self.google_drive_service_account_json) and self.google_drive_folder_id)

    @property
    def youtube_ready(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def amazon_minitv_ready(self) -> bool:
        return bool(self.amazon_minitv_cookies)

    @property
    def readiness_issues(self) -> list[str]:
        issues: list[str] = []
        if self.demo_mode:
            return issues
        if not self.database_url:
            issues.append("DATABASE_URL is missing.")
        if not self.google_drive_ready:
            issues.append("Google Drive service-account configuration is incomplete.")
        if not self.groq_api_key:
            issues.append("GROQ_API_KEY is missing.")
        if not self.youtube_ready:
            issues.append("Google OAuth credentials are missing.")
        return issues

    @property
    def live_ready(self) -> bool:
        return not self.readiness_issues


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()