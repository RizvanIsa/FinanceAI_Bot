from datetime import datetime

from app.config import get_settings
from app.sheets.oauth_client import get_credentials
from app.sheets.client import SheetsClient


def main() -> None:
    """
    Smoke test: подключиться к Google Sheets и добавить одну тестовую строку в лист "Журнал".
    """
    settings = get_settings()

    if not settings.google_oauth_client_path:
        raise ValueError("GOOGLE_OAUTH_CLIENT_PATH is not set in .env")
    if not settings.google_sheets_spreadsheet_id:
        raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")
    if not settings.google_sheets_journal_sheet_name:
        raise ValueError("GOOGLE_SHEETS_JOURNAL_SHEET_NAME is not set in .env")

    creds = get_credentials(settings.google_oauth_client_path)
    client = SheetsClient(creds)

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    op_date = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")  # <-- считаем здесь, вместо ARRAYFORMULA

    # Порядок колонок в "Журнал":
    # created_at, op_date, category, amount, comment_raw, source, tg_user_id, tg_message_id,
    # status, needs_review, month_key, error
    row = [
        created_at,
        op_date,
        "Продукты",
        123,
        "SMOKE TEST: Продукты 123",
        "text",
        0,
        0,
        "ok",
        "FALSE",
        month_key,  # <-- теперь заполняем
        "",
    ]

    result = client.append_row(
        spreadsheet_id=settings.google_sheets_spreadsheet_id,
        sheet_name=settings.google_sheets_journal_sheet_name,
        row_values=row,
    )

    print("✅ Appended row to Google Sheets")
    print(result)


if __name__ == "__main__":
    main()
