import asyncio

from app.config import get_settings
from app.data.category_templates import DEFAULT_TEMPLATE
from app.event_log import clear_event_log, log_event, setup_event_log
from app.llm.client import LLMClient
from app.services.transcribe_service import WhisperTranscriber
from app.sheets.category_repo import CategoryRepo
from app.sheets.client import SheetsClient
from app.sheets.journal_repo import JournalRepo
from app.sheets.oauth_client import get_credentials
from app.telegram.bot import build_bot, build_dispatcher
from app.telegram.handlers import router


async def main() -> None:
    clear_event_log()
    setup_event_log()
    log_event("Бот запускается.")

    settings = get_settings()
    log_event("Настройки загружены из .env.")

    bot = build_bot(settings.telegram_bot_token)
    dp = build_dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    log_event("Удалён webhook Telegram перед запуском polling.")
    log_event("Telegram-бот и обработчики команд готовы.")

    # --- Google Sheets wiring (OAuth) ---
    creds = get_credentials(settings.google_oauth_client_path)
    sheets_client = SheetsClient(creds)
    log_event("Подключение к Google Sheets успешно.")

    journal_repo = JournalRepo(
        sheets_client,
        settings.google_sheets_spreadsheet_id,
        settings.google_sheets_journal_sheet_name,
    )
    dp.workflow_data["journal_repo"] = journal_repo

    category_repo = CategoryRepo(
        sheets_client,
        settings.google_sheets_spreadsheet_id,
        sheet_name="Категории",
    )
    try:
        category_repo.seed_if_empty(DEFAULT_TEMPLATE)
    except Exception as e:
        # Не падаем, если недоступен Google Sheets при старте.
        # Категории уже могут быть созданы ранее; бот продолжит работу.
        log_event(f"Не удалось проверить/заполнить категории при старте: {repr(e)}")
    dp.workflow_data["category_repo"] = category_repo

    # --- LLM wiring ---
    llm = None
    if settings.llm_enabled:
        try:
            llm = LLMClient(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_model,
            )
        except Exception as e:
            log_event(f"LLM не удалось инициализировать, работаем без него: {repr(e)}")
            llm = None
    else:
        log_event("LLM выключен в настройках. Будет использоваться режим pending.")
    dp.workflow_data["llm"] = llm
    if llm is not None:
        log_event("LLM подключен и готов к разбору сообщений.")

    # --- Whisper wiring (transcriber) ---
    transcriber = None
    try:
        transcriber = WhisperTranscriber(
            base_url=settings.llm_base_url,  # тот же провайдер, что и GPT
            api_key=settings.llm_api_key,
            model=settings.whisper_model,
        )
    except Exception as e:
        log_event(f"Распознавание голоса недоступно: {repr(e)}")
        transcriber = None
    dp.workflow_data["transcriber"] = transcriber
    if transcriber is not None:
        log_event("Модуль распознавания голоса подключен.")

    log_event("Бот запущен и ожидает сообщения в Telegram.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_event("Бот остановлен пользователем (Ctrl+C).")
    finally:
        pass
