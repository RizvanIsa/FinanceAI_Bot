import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Timezone (пока используем позже)
    app_timezone: str = os.getenv("APP_TIMEZONE", "Etc/GMT-5")

    # Google Sheets (OAuth)
    google_oauth_client_path: str = os.getenv("GOOGLE_OAUTH_CLIENT_PATH", "")
    google_sheets_spreadsheet_id: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    google_sheets_journal_sheet_name: str = os.getenv("GOOGLE_SHEETS_JOURNAL_SHEET_NAME", "Журнал")
        # LLM (OpenAI-compatible)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_enabled: bool = os.getenv("LLM_ENABLED", "0") == "1"
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-1")




def get_settings() -> Settings:
    """
    Загружает настройки из .env и проверяет обязательные поля.
    """
    s = Settings()

    # Telegram обязателен для запуска бота, но не обязателен для smoke-теста Sheets.
    # Поэтому тут не валим проект, если токена нет.
    if not s.telegram_bot_token:
        # Оставляем предупреждение на будущее, но не падаем.
        pass

    return s
