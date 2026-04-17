from __future__ import annotations

from pathlib import Path

import httpx

from backend.core.config import Settings


class GroqTranscriber:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def ready(self) -> bool:
        return bool(self.settings.groq_api_key)

    def transcribe_to_srt(self, audio_path: Path) -> str:
        if not self.ready:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        with audio_path.open("rb") as audio_file:
            response = httpx.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                data={"model": self.settings.groq_transcription_model, "response_format": "verbose_json"},
                files={"file": (audio_path.name, audio_file, "audio/mpeg")},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        segments = payload.get("segments") or []
        if not segments:
            text = payload.get("text", "")
            return f"1\n00:00:00,000 --> 00:00:05,000\n{text}\n"
        return self._segments_to_srt(segments)

    def _segments_to_srt(self, segments: list[dict]) -> str:
        lines: list[str] = []
        for index, segment in enumerate(segments, start=1):
            start = self._to_srt_timestamp(float(segment.get("start", 0)))
            end = self._to_srt_timestamp(float(segment.get("end", segment.get("start", 0) + 4)))
            lines.extend([str(index), f"{start} --> {end}", str(segment.get("text", "")).strip(), ""])
        return "\n".join(lines)

    @staticmethod
    def _to_srt_timestamp(seconds: float) -> str:
        total_ms = int(seconds * 1000)
        hours, remainder = divmod(total_ms, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, milliseconds = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
