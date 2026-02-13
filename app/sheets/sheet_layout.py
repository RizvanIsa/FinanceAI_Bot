"""
Единый источник истины по структуре листа "Журнал".

Важно:
- Мы НЕ завязываемся на номера колонок в коде, но фиксируем порядок.
- Порядок колонок должен совпадать с заголовками в Google Sheets.
"""

JOURNAL_COLUMNS = [
    "created_at",
    "op_date",
    "category",
    "amount",
    "comment_raw",
    "source",
    "tg_user_id",
    "tg_message_id",
    "status",
    "needs_review",
    "month_key",
    "error",
]
