from __future__ import annotations

from typing import Optional

from app.models.operation import Operation
from app.sheets.client import SheetsClient


class JournalRepo:
    """
    Репозиторий для работы с листом "Журнал".
    - append_operation: добавляет строку
    - is_duplicate: проверяет, записывали ли уже tg_message_id
    - find_last_pending_row: находит последнюю pending строку по tg_user_id
    - update_pending_category: проставляет категорию у найденной pending строки
    - get_pending_summary: достает данные строки для подтверждения пользователю
    """

    def __init__(self, client: SheetsClient, spreadsheet_id: str, sheet_name: str):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

    def append_operation(self, op: Operation) -> dict:
        """
        Добавляет операцию в конец таблицы.
        """
        row = [
            op.created_at,
            op.op_date,
            op.category,
            op.amount,
            op.comment_raw,
            op.source,
            op.tg_user_id,
            op.tg_message_id,
            op.status,
            op.needs_review,
            op.month_key,
            op.error or "",
        ]
        return self.client.append_row(self.spreadsheet_id, self.sheet_name, row)

    def is_duplicate(self, tg_message_id: int) -> bool:
        """
        Проверяет, есть ли уже такая tg_message_id в листе.
        (MVP-реализация: читаем весь столбец tg_message_id и ищем совпадение)
        """
        # H = tg_message_id
        values = self.client.get_column_values(self.spreadsheet_id, self.sheet_name, "H")

        for v in values[1:]:  # пропускаем заголовок
            try:
                if int(v) == int(tg_message_id):
                    return True
            except Exception:
                continue
        return False

    def find_last_pending_row(self, tg_user_id: int) -> Optional[int]:
        """
        Ищет последнюю строку (номер строки в Google Sheets), где:
        - tg_user_id (колонка G) совпадает
        - status (колонка I) == "pending"
        Возвращает номер строки (например 15) или None.
        """
        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:L")
        last_row_index: Optional[int] = None

        for i, row in enumerate(rows[1:], start=2):  # начинаем со строки 2
            try:
                row_user = int(row[6]) if len(row) > 6 and row[6] != "" else None  # G
                row_status = row[8] if len(row) > 8 else ""  # I
            except Exception:
                continue

            if row_user == int(tg_user_id) and row_status == "pending":
                last_row_index = i

        return last_row_index

    def update_pending_category(self, row_index: int, category: str) -> dict:
        """
        Обновляет category, status и needs_review у конкретной строки.
        - category (колонка C)
        - status (колонка I)
        - needs_review (колонка J)
        """
        updates = [
            (f"{self.sheet_name}!C{row_index}", [[category]]),
            (f"{self.sheet_name}!I{row_index}", [["ok"]]),
            (f"{self.sheet_name}!J{row_index}", [["FALSE"]]),
        ]
        return self.client.batch_update_values(self.spreadsheet_id, updates)

    def get_row(self, row_index: int) -> list[str]:
        """
        Возвращает значения строки A:L как список (может быть короче 12, если справа пусто).
        """
        rows = self.client.get_values(
            self.spreadsheet_id,
            self.sheet_name,
            f"A{row_index}:L{row_index}",
        )
        if not rows:
            return []
        return [str(x) for x in rows[0]]

    def get_pending_summary(self, row_index: int) -> dict:
        """
        Достает из строки данные для подтверждения пользователю.
        """
        row = self.get_row(row_index)

        op_date = row[1] if len(row) > 1 else ""
        amount = row[3] if len(row) > 3 else ""
        comment_raw = row[4] if len(row) > 4 else ""

        return {"op_date": op_date, "amount": amount, "comment_raw": comment_raw}
    
    def list_last_rows_for_user(self, tg_user_id: int, limit: int = 10) -> list[tuple[int, str]]:
        """
        Возвращает список последних записей пользователя:
        [(row_index, "09.02.2026 · Продукты · 3000"), ...]
        Берем только status == "ok" (canceled игнорим).
        """
        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:L")
        if not rows or len(rows) < 2:
            return []

        result: list[tuple[int, str]] = []

        # Идем с конца вверх, чтобы быстро собрать последние limit
        for i in range(len(rows) - 1, 0, -1):  # пропускаем заголовок (0)
            row_index = i + 1  # т.к. rows[1] это строка 2
            row = rows[i]

            # индексы по контракту:
            # B op_date = 1, C category = 2, D amount = 3, G tg_user_id = 6, I status = 8
            try:
                row_user = int(row[6]) if len(row) > 6 and row[6] != "" else None
                status = row[8] if len(row) > 8 else ""
            except Exception:
                continue

            if row_user != int(tg_user_id):
                continue
            if status == "canceled":
                continue

            op_date = row[1] if len(row) > 1 else ""
            category = row[2] if len(row) > 2 else ""
            amount = row[3] if len(row) > 3 else ""

            label = f"{op_date} · {category} · {amount}"
            result.append((row_index, label))

            if len(result) >= limit:
                break

        return result

    def update_amount(self, row_index: int, amount: int) -> dict:
        """
        Обновляет amount (колонка D).
        """
        updates = [
            (f"{self.sheet_name}!D{row_index}", [[str(amount)]]),
        ]
        return self.client.batch_update_values(self.spreadsheet_id, updates)
    
    def update_date_and_month_key(self, row_index: int, op_date: str, month_key: str) -> dict:
        # B = op_date, K = month_key
        updates = [
            (f"{self.sheet_name}!B{row_index}", [[op_date]]),
            (f"{self.sheet_name}!K{row_index}", [[month_key]]),
        ]
        return self.client.batch_update_values(self.spreadsheet_id, updates)

    def cancel_row(self, row_index: int) -> dict:
        # I = status, L = error
        updates = [
            (f"{self.sheet_name}!I{row_index}", [["canceled"]]),
            (f"{self.sheet_name}!L{row_index}", [["user_canceled"]]),
        ]
        return self.client.batch_update_values(self.spreadsheet_id, updates)

    def update_category(self, row_index: int, category: str) -> dict:
        """
        Обновляет category у конкретной строки.
        C = category
        """
        updates = [
            (f"{self.sheet_name}!C{row_index}", [[category]]),
        ]
        return self.client.batch_update_values(self.spreadsheet_id, updates)

