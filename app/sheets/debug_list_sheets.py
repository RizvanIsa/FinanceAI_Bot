from app.config import get_settings
from app.sheets.oauth_client import get_credentials
from googleapiclient.discovery import build


def main() -> None:
    settings = get_settings()

    if not settings.google_oauth_client_path:
        raise ValueError("GOOGLE_OAUTH_CLIENT_PATH is not set in .env")
    if not settings.google_sheets_spreadsheet_id:
        raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is not set in .env")

    creds = get_credentials(settings.google_oauth_client_path)
    service = build("sheets", "v4", credentials=creds)

    meta = service.spreadsheets().get(spreadsheetId=settings.google_sheets_spreadsheet_id).execute()
    title = meta.get("properties", {}).get("title", "(no title)")
    sheets = meta.get("sheets", [])

    print(f"Spreadsheet title: {title}")
    print("Sheets:")
    for s in sheets:
        print("-", s.get("properties", {}).get("title"))


if __name__ == "__main__":
    main()
