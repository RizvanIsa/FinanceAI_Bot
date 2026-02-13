from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.data.categories import CATEGORY_CODES, CATEGORY_MAP


def build_categories_keyboard(prefix: str = "cat:") -> InlineKeyboardMarkup:
    """
    Inline-кнопки категорий.
    callback_data хранит КОРОТКИЙ код (чтобы не словить лимит Telegram).

    prefix:
      - "cat:"     для pending
      - "editcat:" для /edit
    """
    buttons = [
        InlineKeyboardButton(text=CATEGORY_MAP[code], callback_data=f"{prefix}{code}")
        for code in CATEGORY_CODES
    ]

    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i + 2])

    return InlineKeyboardMarkup(inline_keyboard=rows)
