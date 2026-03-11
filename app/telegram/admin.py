from __future__ import annotations

from typing import Iterable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.event_log import log_event


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_ids: Iterable[int] | None = None) -> None:
        super().__init__()
        self.allowed = {int(uid) for uid in allowed_user_ids or []}

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        user_id = getattr(user, "id", None)
        if not self.allowed or (user_id is not None and user_id in self.allowed):
            return await handler(event, data)

        log_event(f"Отклонено взаимодействие от пользователя {user_id} (режим админа).")
        return
