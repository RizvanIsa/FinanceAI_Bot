from dataclasses import dataclass
from typing import Optional


@dataclass
class Operation:
    created_at: str        # "YYYY-MM-DD HH:MM:SS"
    op_date: str           # "YYYY-MM-DD" (или как дата в таблице, но пишем строкой)
    category: str
    amount: int
    comment_raw: str
    source: str            # "text" | "voice"
    tg_user_id: int
    tg_message_id: int
    status: str            # "ok" | "pending" | "canceled"
    needs_review: str      # "TRUE" | "FALSE" (строкой, как в Sheets)
    month_key: str         # "YYYY-MM"
    error: Optional[str] = ""
