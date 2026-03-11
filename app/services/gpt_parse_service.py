from datetime import datetime
from typing import Dict, Any, Iterable

from app.data.category_templates import DEFAULT_TEMPLATE
from app.llm.client import LLMClient

DEFAULT_CATEGORY_NAMES = [row["name"] for row in DEFAULT_TEMPLATE]

SYSTEM_PROMPT_TEMPLATE = """
Результат запроса Finbot для телеграм-бота.
Тебе приходит короткое сообщение пользователя (иногда с скобками: 12к, 200k, "две тысячи").
Нужно вернуть ТОЛЬКО JSON по схеме:

{{
  "op_date": "YYYY-MM-DD",        // дата операции. если не указана - сегодня.
  "amount": 12345,               // целое число рублей. если суммы нет - 0.
  "category": "..." ,            // одна из разрешенных категорий или пустая строка
  "needs_review": true/false     // true если категория не уверенная или не удалось определить
}}

Разрешенные категории (строго выбирать из списка):
{categories_section}

Правила:
- Если категория не очевидна или подходит несколько, ставь category="" и needs_review=true
- Если категория понятна, ставь needs_review=false и category = выбранная категория
- Сумму нормализуй: "12к"=12000, "200k"=200000, "две тысячи"=2000
- Если указано "вчера" - op_date = вчера относительно today.
- Валюта всегда рубли.
Верни ТОЛЬКО JSON. Без текста.
""".strip()


def _build_categories_section(category_names: Iterable[str] | None) -> str:
    seen: list[str] = []
    source = list(category_names or [])
    if not source:
        source = [name for name in DEFAULT_CATEGORY_NAMES if name]
    for name in source:
        normalized = (name or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.append(normalized)
    if not seen:
        seen = [name for name in DEFAULT_CATEGORY_NAMES if name]
    return "\n".join(f"- {name}" for name in seen)


def parse_operation_with_gpt(
    llm: LLMClient,
    text: str,
    today: datetime,
    category_names: Iterable[str] | None = None,
) -> Dict[str, Any]:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        categories_section=_build_categories_section(category_names)
    )
    user_prompt = f"""
today={today.strftime("%Y-%m-%d")}
text={text}
""".strip()

    result = llm.chat_json(system=system_prompt, user=user_prompt)

    op_date = str(result.get("op_date", today.strftime("%Y-%m-%d")))
    amount = result.get("amount", 0)
    try:
        amount = int(amount)
    except Exception:
        amount = 0

    category = str(result.get("category", "")).strip()
    needs_review = bool(result.get("needs_review", False))

    return {"op_date": op_date, "amount": amount, "category": category, "needs_review": needs_review}
