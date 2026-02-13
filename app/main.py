import asyncio

from app.config import get_settings
from app.sheets.client import SheetsClient
from app.sheets.journal_repo import JournalRepo
from app.sheets.oauth_client import get_credentials
from app.telegram.bot import build_bot, build_dispatcher
from app.telegram.handlers import router
from app.services.transcribe_service import WhisperTranscriber


async def main() -> None:
    settings = get_settings()

    bot = build_bot(settings.telegram_bot_token)
    dp = build_dispatcher()
    dp.include_router(router)

    # --- Google Sheets wiring (OAuth) ---
    # token.json у тебя уже появился ранее, поэтому браузер чаще всего больше не откроется.
    creds = get_credentials(settings.google_oauth_client_path)
    sheets_client = SheetsClient(creds)
    journal_repo = JournalRepo(
        sheets_client,
        settings.google_sheets_spreadsheet_id,
        settings.google_sheets_journal_sheet_name,
    )

    # Передаем repo в aiogram workflow_data, чтобы хендлеры могли его получить через DI
    dp.workflow_data["journal_repo"] = journal_repo
    from app.llm.client import LLMClient

    llm = None
    try:
        from app.llm.client import LLMClient

        llm = None
        if settings.llm_enabled:
            try:
                llm = LLMClient(
                    base_url=settings.llm_base_url,
                    api_key=settings.llm_api_key,
                    model=settings.llm_model,
                )
            except Exception:
                print("⚠️ LLM init failed, LLM disabled")
    except Exception as e:
        print("⚠️ LLM init failed, LLM disabled:", repr(e))

    dp.workflow_data["llm"] = llm

        # --- Whisper wiring (transcriber) ---
    transcriber = None
    try:
        transcriber = WhisperTranscriber(
            base_url=settings.llm_base_url,   # тот же провайдер, что и GPT
            api_key=settings.llm_api_key,
            model=settings.whisper_model,
        )
    except Exception as e:
        print("⚠️ Transcriber init failed:", repr(e))
        transcriber = None

    dp.workflow_data["transcriber"] = transcriber

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Остановлено пользователем (Ctrl+C)")

