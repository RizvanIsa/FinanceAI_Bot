import os
import uuid
import asyncio

from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.llm.client import LLMClient
from app.services.ingest_service import (
    build_pending_operation_from_text,
    build_operation_from_text_with_gpt,
)
from app.services.transcribe_service import WhisperTranscriber
from app.sheets.journal_repo import JournalRepo
from app.telegram.keyboards import build_categories_keyboard
from app.telegram.states import EditJournalStates

router = Router()


# ----------------------------
# Helpers for /edit UI
# ----------------------------

def build_edit_rows_keyboard(rows: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = []
    for row_index, label in rows:
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"edit:row:{row_index}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_edit_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Дата", callback_data="edit:action:date"),
                InlineKeyboardButton(text="Сумма", callback_data="edit:action:amount"),
            ],
            [
                InlineKeyboardButton(text="Категория", callback_data="edit:action:category"),
                InlineKeyboardButton(text="Отменить", callback_data="edit:action:cancel"),
            ],
            [
                InlineKeyboardButton(text="✅ Завершить", callback_data="edit:done"),
            ],
        ]
    )



def build_edit_cancel_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="edit:confirm_cancel"),
                InlineKeyboardButton(text="Нет", callback_data="edit:back"),
            ]
        ]
    )


def format_edit_card(op_date: str, category: str, amount: str) -> str:
    return f"{op_date} · {category} · {amount} ₽\n\n<b>Что изменить?</b>"

async def edit_flash_message(
    obj: object,
    state: FSMContext,
    text: str,
    seconds: float = 0.8,
) -> None:
    """
    Коротко показывает текст в том же menu_message (через edit_message),
    потом возвращаемся к карточке.
    """
    data = await state.get_data()
    menu_message_id = data.get("menu_message_id")
    chat_id = data.get("menu_chat_id")
    if not (menu_message_id and chat_id):
        return

    bot = obj.bot  # Message/CallbackQuery имеют .bot
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=menu_message_id,
        text=text,
        parse_mode="HTML",
    )
    await asyncio.sleep(seconds)


async def edit_render_actions(
    callback_or_message: object,
    journal_repo: JournalRepo,
    state: FSMContext,
    row_index: int,
) -> None:
    """
    Рисует карточку записи + кнопки действий через edit_message.
    Работает как из callback, так и из text-handler.
    """
    row = journal_repo.get_row(row_index)
    if not row:
        # fallback: просто очистим состояние
        await state.clear()
        return

    op_date = row[1] if len(row) > 1 else ""
    category = row[2] if len(row) > 2 else ""
    amount = row[3] if len(row) > 3 else ""

    text = format_edit_card(op_date, category, amount)

    data = await state.get_data()
    menu_message_id = data.get("menu_message_id")
    chat_id = data.get("menu_chat_id")

    # Если у нас сохранен menu_message_id - редактируем именно его.
    if menu_message_id and chat_id:
        bot = callback_or_message.bot  # Message/CallbackQuery имеют .bot
        try:
            await bot.edit_message_text(
        chat_id=chat_id,
        message_id=menu_message_id,
        text=text,
        reply_markup=build_edit_actions_keyboard(),
        parse_mode="HTML",
    )
        except Exception as e:
    # Telegram ругается, если мы пытаемся изменить сообщение на точно такое же
            if "message is not modified" not in str(e):
                raise

    else:
        # fallback: редактируем текущее сообщение
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(
                text,
                reply_markup=build_edit_actions_keyboard(),
                parse_mode="HTML",
            )
        elif isinstance(callback_or_message, Message):
            await callback_or_message.answer(
                text,
                reply_markup=build_edit_actions_keyboard(),
                parse_mode="HTML",
            )

    await state.set_state(EditJournalStates.choosing_action)
    await state.update_data(row_index=row_index)


# ----------------------------
# Basic commands
# ----------------------------

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Я жив ✅")


# ----------------------------
# /edit flow
# ----------------------------

@router.message(Command("edit"))
async def edit_menu_entry(
    message: Message,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    tg_user_id = message.from_user.id if message.from_user else 0
    rows = journal_repo.list_last_rows_for_user(tg_user_id=tg_user_id, limit=10)

    if not rows:
        await message.answer("Не нашел ваших записей для редактирования.")
        return

    text = "Редактирование: выберите запись из последних 10."
    sent = await message.answer(text, reply_markup=build_edit_rows_keyboard(rows))

    await state.set_state(EditJournalStates.selecting_row)
    await state.update_data(
        tg_user_id=tg_user_id,
        menu_message_id=sent.message_id,
        menu_chat_id=sent.chat.id,
    )


@router.callback_query(F.data.startswith("edit:row:"))
async def edit_select_row(
    callback: CallbackQuery,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    data = callback.data or ""
    row_index = int(data.split(":")[-1])

    # фиксируем menu message id, чтобы дальше всегда редактировать одно и то же сообщение
    await state.update_data(
        menu_message_id=callback.message.message_id,
        menu_chat_id=callback.message.chat.id,
        row_index=row_index,
    )

    await edit_render_actions(callback, journal_repo, state, row_index=row_index)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:action:"))
async def edit_choose_action(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    action = (callback.data or "").split(":")[-1]
    data = await state.get_data()
    row_index = data.get("row_index")

    if not row_index:
        await callback.answer()
        await state.clear()
        return

    if action == "amount":
        await callback.message.edit_text("Введите новую сумму числом:")
        await state.set_state(EditJournalStates.waiting_amount)

    elif action == "date":
        await callback.message.edit_text("Введите новую дату в формате DD.MM.YYYY:")
        await state.set_state(EditJournalStates.waiting_date)

    elif action == "category":
        await callback.message.edit_text(
            "Выберите новую категорию:",
            reply_markup=build_categories_keyboard(prefix="editcat:"),
        )
        await state.set_state(EditJournalStates.choosing_category)

    elif action == "cancel":
        await callback.message.edit_text(
            "Вы уверены, что хотите отменить запись?",
            reply_markup=build_edit_cancel_confirm_keyboard(),
        )
        await state.set_state(EditJournalStates.confirming_cancel)

    await callback.answer()


@router.message(EditJournalStates.waiting_amount, F.text)
async def edit_waiting_amount(
    message: Message,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    row_index = data.get("row_index")

    if not row_index:
        await state.clear()
        return

    raw = (message.text or "").strip().replace(" ", "")
    if not raw.isdigit():
        await message.answer("Введите сумму числом, например: 3000")
        return

    amount = int(raw)
    journal_repo.update_amount(row_index=row_index, amount=amount)

    await edit_flash_message(message, state, f"✅ Сумма обновлена: <b>{amount}</b> ₽")
    await edit_render_actions(message, journal_repo, state, row_index=row_index)


@router.message(EditJournalStates.waiting_date, F.text)
async def edit_waiting_date(
    message: Message,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    row_index = data.get("row_index")

    if not row_index:
        await state.clear()
        return

    raw = (message.text or "").strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d")
    except Exception:
        await message.answer("Введите дату строго в формате DD.MM.YYYY, например: 09.02.2026")
        return

    today = datetime.now()
    if dt.date() > today.date():
        await message.answer("Дата в будущем. Введите дату не позже сегодняшней.")
        return

    if dt < (today - timedelta(days=31)):
        await message.answer("Слишком старая дата. Можно править не дальше чем на 1 месяц назад.")
        return

    op_date = dt.strftime("%d.%m.%Y")
    month_key = dt.strftime("%Y-%m")

    journal_repo.update_date_and_month_key(row_index=row_index, op_date=op_date, month_key=month_key)
    await edit_flash_message(message, state, f"✅ Дата обновлена: <b>{op_date}</b>")
    await edit_render_actions(message, journal_repo, state, row_index=row_index)



@router.callback_query(F.data.startswith("editcat:"))
async def edit_category_pick(
    callback: CallbackQuery,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    code = (callback.data or "").split("editcat:", 1)[1].strip()

    from app.data.categories import CATEGORY_MAP

    if code not in CATEGORY_MAP:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    data = await state.get_data()
    row_index = data.get("row_index")
    if not row_index:
        await callback.answer()
        await state.clear()
        return

    category = CATEGORY_MAP[code]
    journal_repo.update_category(row_index=row_index, category=category)
    await edit_flash_message(callback, state, f"✅ Категория обновлена: <b>{category}</b>")
    await edit_render_actions(callback, journal_repo, state, row_index=row_index)

    await edit_render_actions(callback, journal_repo, state, row_index=row_index)
    await callback.answer("Готово ✅")


@router.callback_query(F.data == "edit:confirm_cancel")
async def edit_confirm_cancel(
    callback: CallbackQuery,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    row_index = data.get("row_index")

    if not row_index:
        await callback.answer()
        await state.clear()
        return

    journal_repo.cancel_row(row_index=row_index)

    # покажем текстом и выйдем из режима /edit
    await callback.message.edit_text("Запись отменена ✅")
    await callback.answer("Отменено ✅")
    await state.clear()


@router.callback_query(F.data == "edit:back")
async def edit_back_to_actions(
    callback: CallbackQuery,
    journal_repo: JournalRepo,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    row_index = data.get("row_index")

    if not row_index:
        await callback.answer()
        await state.clear()
        return

    await edit_render_actions(callback, journal_repo, state, row_index=row_index)
    await callback.answer()

@router.callback_query(F.data == "edit:done")
async def edit_done(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    # Убираем режим редактирования
    await state.clear()

    # Закрываем меню (убираем кнопки)
    try:
        await callback.message.edit_text("Редактирование завершено ✅")
    except Exception:
        pass

    await callback.answer()


# ----------------------------
# Main ingest: text
# ----------------------------

@router.message(F.text)
async def any_text_handler(
    message: Message,
    journal_repo: JournalRepo,
    llm: Optional[LLMClient],
    state: FSMContext,
) -> None:
    # Если пользователь в режиме /edit - не принимаем как новую операцию
    if await state.get_state() is not None:
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return

    tg_user_id = message.from_user.id if message.from_user else 0
    tg_message_id = message.message_id

    if journal_repo.is_duplicate(tg_message_id):
        await message.answer("Это сообщение уже записано. Дубль пропущен ✅")
        return

    # пробуем GPT, но без риска упасть
    try:
        if llm is None:
            raise RuntimeError("LLM disabled or not configured")

        op = build_operation_from_text_with_gpt(
            llm=llm,
            text=text,
            tg_user_id=tg_user_id,
            tg_message_id=tg_message_id,
            source="text",
        )

    except Exception as e:
        if isinstance(e, RuntimeError) and "LLM disabled" in str(e):
            print("ℹ️ LLM выключен: pending-first")
        else:
            print("⚠️ LLM error, fallback to pending:", repr(e))

        op = build_pending_operation_from_text(
            text=text,
            tg_user_id=tg_user_id,
            tg_message_id=tg_message_id,
            source="text",
        )

    journal_repo.append_operation(op)

    if op.status == "pending":
        await message.answer("Уточните категорию:", reply_markup=build_categories_keyboard())
        return

    await message.answer(f"Записал ✅ {op.op_date} · {op.category} · {op.amount} ₽")


# ----------------------------
# Main ingest: voice
# ----------------------------

@router.message(F.voice)
async def any_voice_handler(
    message: Message,
    journal_repo: JournalRepo,
    llm: Optional[LLMClient],
    transcriber: Optional[WhisperTranscriber],
) -> None:
    tg_user_id = message.from_user.id if message.from_user else 0
    tg_message_id = message.message_id

    if journal_repo.is_duplicate(tg_message_id):
        await message.answer("Это голосовое сообщение уже записано. Дубль пропущен ✅")
        return

    tmp_dir = "app/tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}.ogg"
    file_path = os.path.join(tmp_dir, filename)

    try:
        bot = message.bot
        file = await bot.get_file(message.voice.file_id)
        await bot.download_file(file.file_path, destination=file_path)

        if transcriber is None:
            await message.answer(
                "Распознавание голоса недоступно. "
                "Отправьте сумму текстом или запишите голосовое еще раз."
            )
            return

        try:
            tr = transcriber.transcribe_ogg(file_path)
            text = tr.text.strip()
        except Exception as e:
            print("⚠️ Whisper error:", repr(e))
            await message.answer(
                "Не удалось распознать голос. "
                "Отправьте сумму текстом или запишите голосовое еще раз."
            )
            return

        if not text:
            await message.answer(
                "Не удалось распознать голос. "
                "Отправьте сумму текстом или запишите голосовое еще раз."
            )
            return

        try:
            if llm is None:
                raise RuntimeError("LLM disabled or not configured")

            op = build_operation_from_text_with_gpt(
                llm=llm,
                text=text,
                tg_user_id=tg_user_id,
                tg_message_id=tg_message_id,
                source="voice",
            )
        except Exception as e:
            print("⚠️ LLM error, fallback to pending:", repr(e))
            op = build_pending_operation_from_text(
                text=text,
                tg_user_id=tg_user_id,
                tg_message_id=tg_message_id,
                source="voice",
            )

        try:
            amount = int(op.amount or 0)
        except Exception:
            amount = 0

        if amount == 0:
            await message.answer(
                f"Распознал: \"{text}\", но не нашел сумму.\n"
                f"Отправьте сумму текстом или запишите голосовое еще раз."
            )
            return

        journal_repo.append_operation(op)

        if op.status == "pending":
            await message.answer(
                f"Распознал: \"{text}\".\nУточните категорию:",
                reply_markup=build_categories_keyboard(),
            )
            return

        await message.answer(f"Записал ✅ {op.op_date} · {op.category} · {op.amount} ₽")

    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass


# ----------------------------
# Pending category picker (cat:)
# ----------------------------

@router.callback_query(F.data.startswith("cat:"))
async def category_callback_handler(
    callback: CallbackQuery,
    journal_repo: JournalRepo,
) -> None:
    data = callback.data or ""
    code = data.split("cat:", 1)[1].strip()

    from app.data.categories import CATEGORY_MAP

    if code not in CATEGORY_MAP:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    category = CATEGORY_MAP[code]
    tg_user_id = callback.from_user.id if callback.from_user else 0

    row_index = journal_repo.find_last_pending_row(tg_user_id=tg_user_id)
    if not row_index:
        await callback.answer()
        await callback.message.answer("Не нашел запись для уточнения. Попробуйте отправить сообщение заново.")
        return

    summary = journal_repo.get_pending_summary(row_index=row_index)
    op_date = summary.get("op_date", "")
    amount = summary.get("amount", "")

    journal_repo.update_pending_category(row_index=row_index, category=category)

    await callback.answer()

    # удаляем сообщение с кнопками, чтобы не мусорить
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(f"Записал ✅ {op_date} · {category} · {amount} ₽")
