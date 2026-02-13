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

        Мы просим: output ONLY JSON. Потом парсим.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Некоторые провайдеры поддерживают response_format, некоторые нет.
            # Мы не зависим от этого, но можно включить - если поддерживается, станет еще надежнее.
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"LLM returned non-JSON: {content}") from e
