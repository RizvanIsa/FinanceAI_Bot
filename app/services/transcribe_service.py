from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class TranscribeResult:
    text: str


class WhisperTranscriber:
    """
    OpenAI-compatible transcriber.
    Работает и с Artemox (если проксирует /v1/audio/transcriptions),
    и с прямым OpenAI (https://api.openai.com/v1).
    """

    def __init__(self, base_url: str, api_key: str, model: str = "whisper-1", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def transcribe_ogg(self, file_path: str) -> TranscribeResult:
        url = f"{self.base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # multipart/form-data
        with open(file_path, "rb") as f:
            files = {"file": ("voice.ogg", f, "audio/ogg")}
            data = {"model": self.model}

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, data=data, files=files)
                resp.raise_for_status()
                payload = resp.json()

        text = (payload.get("text") or "").strip()
        return TranscribeResult(text=text)
