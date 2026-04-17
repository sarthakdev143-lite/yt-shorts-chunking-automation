from __future__ import annotations

import mimetypes
from pathlib import Path

import boto3
from botocore.config import Config

from backend.core.config import Settings


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    @property
    def ready(self) -> bool:
        return self.settings.r2_ready

    def _client_for_r2(self):
        if not self.ready:
            raise RuntimeError("Cloudflare R2 is not configured.")
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.cloudflare_r2_endpoint,
                aws_access_key_id=self.settings.cloudflare_r2_access_key,
                aws_secret_access_key=self.settings.cloudflare_r2_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._client

    def generate_presigned_upload(self, object_key: str, content_type: str) -> dict[str, str | None]:
        client = self._client_for_r2()
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.settings.cloudflare_r2_bucket_name,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
        return {"url": url, "method": "PUT", "object_key": object_key, "public_url": self.public_url_for(object_key)}

    def public_url_for(self, object_key: str) -> str | None:
        if self.settings.cloudflare_r2_public_base_url:
            return f"{self.settings.cloudflare_r2_public_base_url.rstrip('/')}/{object_key}"
        return None

    def download_object(self, object_key: str, destination: Path) -> Path:
        client = self._client_for_r2()
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(self.settings.cloudflare_r2_bucket_name, object_key, str(destination))
        return destination

    def upload_file(self, source: Path, object_key: str, content_type: str | None = None) -> str:
        client = self._client_for_r2()
        guessed_type, _ = mimetypes.guess_type(source.name)
        client.upload_file(
            str(source),
            self.settings.cloudflare_r2_bucket_name,
            object_key,
            ExtraArgs={"ContentType": content_type or guessed_type or "application/octet-stream"},
        )
        return self.public_url_for(object_key) or object_key

    def delete_object(self, object_key: str) -> None:
        client = self._client_for_r2()
        client.delete_object(Bucket=self.settings.cloudflare_r2_bucket_name, Key=object_key)
