from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "Shortsmith API"
    environment: str = "development"
    api_prefix: str = "/api"
    demo_mode: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    data_seed_path: str = str(Path("data") / "demo-projects.json")

    database_url: str | None = None
    groq_api_key: str | None = None
    groq_transcription_model: str = "whisper-large-v3-turbo"

    cloudflare_r2_access_key: str | None = None
    cloudflare_r2_secret_key: str | None = None
    cloudflare_r2_bucket_name: str | None = None
    cloudflare_r2_endpoint: str | None = None
    cloudflare_r2_public_base_url: str | None = None

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    upstash_redis_url: str | None = None

    google_client_id: str | None = None
    google_client_secret: str | None = None
    nextauth_secret: str | None = None

    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def root_path(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def resolved_seed_path(self) -> Path:
        return (self.root_path / self.data_seed_path).resolve()

    @property
    def r2_ready(self) -> bool:
        return all(
            [
                self.cloudflare_r2_access_key,
                self.cloudflare_r2_secret_key,
                self.cloudflare_r2_bucket_name,
                self.cloudflare_r2_endpoint,
            ]
        )

    @property
    def youtube_ready(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
