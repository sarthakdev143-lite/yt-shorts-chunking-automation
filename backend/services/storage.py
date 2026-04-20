from __future__ import annotations

import io
import mimetypes
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from backend.core.config import Settings

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._service = None

    @property
    def ready(self) -> bool:
        return self.settings.google_drive_ready

    def _service_for_drive(self):
        if not self.ready:
            raise RuntimeError("Google Drive storage is not configured.")
        if self._service is None:
            credentials = Credentials.from_service_account_file(self.settings.google_drive_service_account_file, scopes=DRIVE_SCOPES)
            self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    def public_url_for(self, file_id: str) -> str:
        return f"https://drive.google.com/uc?id={file_id}&export=download"

    def upload_file(self, source: Path, object_key: str, content_type: str | None = None) -> str:
        service = self._service_for_drive()
        guessed_type, _ = mimetypes.guess_type(source.name)
        media = MediaFileUpload(str(source), mimetype=content_type or guessed_type or "application/octet-stream", resumable=True)
        metadata = {
            "name": object_key.replace("/", "__"),
            "parents": [self.settings.google_drive_folder_id],
            "appProperties": {"objectKey": object_key},
        }
        file = (
            service.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink, webContentLink")
            .execute()
        )
        self._ensure_public_reader(file["id"])
        return file["id"]

    def download_object(self, object_key: str, destination: Path) -> Path:
        service = self._service_for_drive()
        file_id = self._resolve_file_id(object_key)
        request = service.files().get_media(fileId=file_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            downloader = MediaIoBaseDownload(handle, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return destination

    def delete_object(self, object_key: str) -> None:
        service = self._service_for_drive()
        service.files().delete(fileId=self._resolve_file_id(object_key)).execute()

    def _resolve_file_id(self, object_key: str) -> str:
        if object_key.startswith("drive:"):
            return object_key.removeprefix("drive:")
        service = self._service_for_drive()
        query = (
            "trashed = false "
            f"and '{self.settings.google_drive_folder_id}' in parents "
            f"and appProperties has {{ key='objectKey' and value='{object_key}' }}"
        )
        response = service.files().list(q=query, spaces="drive", fields="files(id, name)", pageSize=1).execute()
        files = response.get("files", [])
        if not files:
            raise FileNotFoundError(f"Google Drive file not found for object key: {object_key}")
        return files[0]["id"]

    def _ensure_public_reader(self, file_id: str) -> None:
        service = self._service_for_drive()
        service.permissions().create(fileId=file_id, body={"type": "anyone", "role": "reader"}).execute()
