from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.sheets.category_repo import Category


def build_categories_keyboard(categories: list[Category], prefix: str = "cat:") -> InlineKeyboardMarkup:
    """
    Inline-кнопки категорий.
    callback_data хранит category_id.
    prefix:
      - "cat:" для pending
      - "editcat:" для /edit
    """
    buttons = [
        InlineKeyboardButton(text=c.name, callback_data=f"{prefix}{c.category_id}")
        for c in categories
    ]

    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i + 2])

    return InlineKeyboardMarkup(inline_keyboard=rows)