from typing import Any, List, Tuple

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class SheetsClient:
    """
    Мини-клиент для работы с Google Sheets.

    На MVP нам нужны операции:
    - append_row: добавить строку в конец листа
    - get_values: прочитать диапазон
    - get_column_values: прочитать один столбец
    - batch_update_values: обновить несколько ячеек/диапазонов одним запросом
    """

    def __init__(self, creds: Credentials):
        self._service = build("sheets", "v4", credentials=creds)

    def append_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row_values: List[Any],
    ) -> dict:
        """
        Добавляет строку в конец листа.
        """
        range_name = f"{sheet_name}!A:Z"
        body = {"values": [row_values]}

        result = (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        return result

    def get_values(self, spreadsheet_id: str, sheet_name: str, a1_range: str) -> List[List[Any]]:
        """
        Читает значения из указанного диапазона.
        Пример: a1_range="A:L"
        """
        range_name = f"{sheet_name}!{a1_range}"
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])

    def get_column_values(self, spreadsheet_id: str, sheet_name: str, column_letter: str) -> List[Any]:
        """
        Читает значения одного столбца целиком.
        Пример: column_letter="H"
        Возвращает список значений (без разбиения на строки/колонки).
        """
        values = self.get_values(spreadsheet_id, sheet_name, f"{column_letter}:{column_letter}")
        # values это список строк, где каждая строка - список из 0 или 1 элемента
        return [row[0] if row else "" for row in values]

    def batch_update_values(self, spreadsheet_id: str, updates: List[Tuple[str, List[List[Any]]]]) -> dict:
        """
        Пакетное обновление нескольких диапазонов.

        updates: список кортежей:
        - range_name: например "Журнал!C10"
        - values: например [[ "Продукты" ]]
        """
        data = [{"range": r, "values": v} for r, v in updates]
        body = {"valueInputOption": "USER_ENTERED", "data": data}

        result = (
            self._service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
            .execute()
        )
        return result
