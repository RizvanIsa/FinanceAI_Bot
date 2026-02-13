from datetime import datetime, timedelta
from typing import Dict, Any

from app.llm.client import LLMClient
from app.llm.prompts import CATEGORIES


SYSTEM_PROMPT = f"""
Ты парсер финансовых операций для телеграм-бота.
Тебе приходит короткое сообщение пользователя (иногда с сокращениями: 12к, 200k, "две тысячи").
Нужно вернуть ТОЛЬКО JSON по схеме:

{{
  "op_date": "YYYY-MM-DD",        // дата операции. если не указана - сегодня.
  "amount": 12345,               // целое число рублей. если суммы нет - 0.
  "category": "..." ,            // одна из разрешенных категорий или пустая строка
  "needs_review": true/false     // true если категория не уверенная или не удалось определить
}}

Разрешенные категории (строго выбирать из списка):
{CATEGORIES}

Правила:
- Если категория не очевидна или подходит несколько, ставь category="" и needs_review=true
- Если категория понятна, ставь needs_review=false и category = выбранная категория
- Сумму нормализуй: "12к"=12000, "200k"=200000, "две тысячи"=2000
- Если указано "вчера" - op_date = вчера относительно today.
- Валюта всегда рубли.
Верни ТОЛЬКО JSON. Без текста.
""".strip()


def parse_operation_with_gpt(
    llm: LLMClient,
    text: str,
    today: datetime,
) -> Dict[str, Any]:
    user_prompt = f"""
today={today.strftime("%Y-%m-%d")}
text={text}
""".strip()

    result = llm.chat_json(system=SYSTEM_PROMPT, user=user_prompt)

    # минимальная нормализация/страховка типов
    op_date = str(result.get("op_date", today.strftime("%Y-%m-%d")))
    amount = result.get("amount", 0)
    try:
        amount = int(amount)
    except Exception:
        amount = 0

    category = str(result.get("category", "")).strip()
    needs_review = bool(result.get("needs_review", False))

    # финальный dict
    return {"op_date": op_date, "amount": amount, "category": category, "needs_review": needs_review}
