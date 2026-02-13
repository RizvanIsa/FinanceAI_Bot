from datetime import datetime

from app.config import get_settings
from app.models.operation import Operation
from app.sheets.client import SheetsClient
from app.sheets.journal_repo import JournalRepo
from app.sheets.oauth_client import get_credentials


def main() -> None:
    settings = get_settings()

    creds = get_credentials(settings.google_oauth_client_path)
    client = SheetsClient(creds)
    repo = JournalRepo(
        client,
        settings.google_sheets_spreadsheet_id,
        settings.google_sheets_journal_sheet_name,
    )

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    op_date = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")

    # 1) Добавим pending запись (как будто GPT сказал needs_review)
    op = Operation(
        created_at=created_at,
        op_date=op_date,
        category="",  # пусто, будем выбирать кнопкой
        amount=777,
        comment_raw="TEST PENDING: Продукты 777",
        source="text",
        tg_user_id=123,
        tg_message_id=999001,
        status="pending",
        needs_review="TRUE",
        month_key=month_key,
        error="",
    )

    print("Appending pending operation...")
    repo.append_operation(op)

    # 2) Найдем последнюю pending строку
    row_index = repo.find_last_pending_row(tg_user_id=123)
    print("Last pending row index:", row_index)

    if row_index:
        # 3) Обновим категорию как будто нажали кнопку
        print("Updating category on pending row...")
        repo.update_pending_category(row_index=row_index, category="Продукты")
        print("✅ Updated")
    else:
        print("❌ Pending row not found")


if __name__ == "__main__":
    main()
