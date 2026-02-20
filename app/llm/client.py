import json
from typing import Any, Dict

import httpx


class LLMClient:
    """
    Мини-клиент под OpenAI-compatible Chat Completions API.

    Ожидаем endpoint:
      POST {base_url}/chat/completions
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 30.0):
        if not base_url:
            raise ValueError("LLM_BASE_URL is empty")
        if not api_key:
            raise ValueError("LLM_API_KEY is empty")
        if not model:
            raise ValueError("LLM_MODEL is empty")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s

    def chat_json(self, system: str, user: str) -> Dict[str, Any]:
        """
        Возвращает dict (JSON), который модель обязана выдать.
        Делаем 2 попытки:
        1) с response_format (если провайдер поддерживает)
        2) без response_format (fallback)
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        base_payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        def _extract_json(resp_json: Dict[str, Any]) -> Dict[str, Any]:
            try:
                content = resp_json["choices"][0]["message"]["content"]
            except Exception as e:
                raise ValueError(f"LLM bad response shape: {resp_json}") from e

            if content is None or str(content).strip() == "":
                raise ValueError("LLM returned empty content")

            try:
                return json.loads(content)
            except Exception as e:
                raise ValueError(f"LLM returned non-JSON: {content}") from e

        with httpx.Client(timeout=self.timeout_s) as client:
            # Try 1: with response_format
            payload = dict(base_payload)
            payload["response_format"] = {"type": "json_object"}
            try:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return _extract_json(resp.json())
            except Exception:
                # Try 2: without response_format
                resp = client.post(url, headers=headers, json=base_payload)
                resp.raise_for_status()
                return _extract_json(resp.json())