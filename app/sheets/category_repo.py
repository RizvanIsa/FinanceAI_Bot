from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import Optional

from app.sheets.client import SheetsClient


@dataclass(frozen=True)
class Category:
    category_id: str
    name: str
    section: str
    order: int
    is_active: bool


class CategoryRepo:
    """
    Лист: "Категории"
    Колонки (A:E):
    A category_id
    B name
    C section
    D order
    E is_active  (TRUE/FALSE)
    """

    def __init__(self, client: SheetsClient, spreadsheet_id: str, sheet_name: str = "Категории"):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

    def list_active(self) -> list[Category]:
        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:E")
        if not rows or len(rows) < 2:
            return []

        result: list[Category] = []
        for r in rows[1:]:
            if len(r) < 5:
                continue

            category_id = str(r[0]).strip()
            name = str(r[1]).strip()
            section = str(r[2]).strip()
            try:
                order = int(str(r[3]).strip())
            except Exception:
                order = 0

            is_active_raw = str(r[4]).strip().lower()
            is_active = is_active_raw in ("true", "1", "yes", "y", "да")

            if not category_id or not name:
                continue
            if not is_active:
                continue

            result.append(
                Category(
                    category_id=category_id,
                    name=name,
                    section=section,
                    order=order,
                    is_active=is_active,
                )
            )

        # section -> order -> name
        result.sort(key=lambda c: (c.section, c.order, c.name))
        return result

    def get_name_by_id(self, category_id: str) -> Optional[str]:
        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:B")
        if not rows or len(rows) < 2:
            return None
        for r in rows[1:]:
            if len(r) < 2:
                continue
            if str(r[0]).strip() == category_id:
                return str(r[1]).strip()
        return None

    def find_id_by_name(self, name: str) -> Optional[str]:
        """
        Нужен для GPT-режима: GPT вернул category как текст (name),
        мы пытаемся найти соответствующий category_id.
        Сравнение делаем по нормализованной строке.
        """
        target = (name or "").strip().lower()
        if not target:
            return None

        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:B")
        if not rows or len(rows) < 2:
            return None

        for r in rows[1:]:
            if len(r) < 2:
                continue
            cid = str(r[0]).strip()
            nm = str(r[1]).strip().lower()
            if cid and nm == target:
                return cid

    def _find_row_index(self, category_id: str) -> Optional[int]:
        if not category_id:
            return None
        rows = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:A")
        if not rows:
            return None
        for idx, row in enumerate(rows, start=1):
            if idx == 1:
                continue
            if not row:
                continue
            if str(row[0]).strip() == category_id:
                return idx
        return None

    def _next_order(self, section: str) -> int:
        section = (section or "custom").strip()
        current = self.list_active()
        max_order = 0
        for cat in current:
            if cat.section == section and isinstance(cat.order, int):
                max_order = max(max_order, cat.order)
        return max_order + 10

    def update_name(self, category_id: str, new_name: str) -> bool:
        if not category_id or not new_name:
            return False
        row_idx = self._find_row_index(category_id)
        if row_idx is None:
            return False
        self.client.batch_update_values(
            self.spreadsheet_id,
            [(f"{self.sheet_name}!B{row_idx}", [[new_name.strip()]])],
        )
        return True

    def deactivate_category(self, category_id: str) -> bool:
        row_idx = self._find_row_index(category_id)
        if row_idx is None:
            return False
        self.client.batch_update_values(
            self.spreadsheet_id,
            [(f"{self.sheet_name}!E{row_idx}", [["FALSE"]])],
        )
        return True

    def add_category(
        self,
        name: str,
        section: str = "custom",
        order: Optional[int] = None,
        is_active: bool = True,
    ) -> str:
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Category name cannot be empty")
        category_id = f"user_{uuid.uuid4().hex[:8]}"
        final_order = order if order is not None else self._next_order(section)
        self.client.append_row(
            self.spreadsheet_id,
            self.sheet_name,
            [
                category_id,
                normalized_name,
                section or "custom",
                str(final_order),
                "TRUE" if is_active else "FALSE",
            ],
        )
        return category_id
        return None

    def seed_if_empty(self, rows: list[dict]) -> None:
        """
        Если лист пустой или в нем только заголовок - заливаем категории шаблона.
        """
        existing = self.client.get_values(self.spreadsheet_id, self.sheet_name, "A:E")

        # Лист совсем пустой -> создаем заголовок
        if not existing:
            self.client.append_row(
                self.spreadsheet_id,
                self.sheet_name,
                ["category_id", "name", "section", "order", "is_active"],
            )
            existing = [["category_id", "name", "section", "order", "is_active"]]

        # Если есть хотя бы одна строка данных кроме заголовка - ничего не делаем
        if len(existing) > 1:
            return

        # Заливаем шаблон
        for r in rows:
            self.client.append_row(
                self.spreadsheet_id,
                self.sheet_name,
                [
                    r["category_id"],
                    r["name"],
                    r["section"],
                    str(r["order"]),
                    "TRUE" if r.get("is_active", True) else "FALSE",
                ],
            )
