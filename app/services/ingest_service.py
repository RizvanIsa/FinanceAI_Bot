import re
from datetime import datetime

from app.models.operation import Operation


def _parse_amount_test(text: str) -> int:
    """
    ВРЕМЕННЫЙ тестовый парсер суммы (только для этапа 4.1).
    Ищет последнюю группу цифр в сообщении:
      "Продукты 3000" -> 3000
      "Одежда 5 000" -> 5000
    Если цифр нет -> 0
    """
    matches = re.findall(r"(\d[\d\s]*)", text)
    if not matches:
        return 0
    last = matches[-1].replace(" ", "")
    try:
        return int(last)
    except Exception:
        return 0


def build_pending_operation_from_text(
    text: str,
    tg_user_id: int,
    tg_message_id: int,
    source: str = "text",
) -> Operation:
    """
    Создает pending-операцию из текста.
    На этом этапе мы всегда пишем pending и просим выбрать категорию кнопкой.
    """
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    op_date = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")

    amount = _parse_amount_test(text)

    return Operation(
        created_at=created_at,
        op_date=op_date,
        category="",  # выберем кнопкой
        amount=amount,
        comment_raw=text,
        source=source,
        tg_user_id=tg_user_id,
        tg_message_id=tg_message_id,
        status="pending",
        needs_review="TRUE",
        month_key=month_key,
        error="",
    )


from app.llm.client import LLMClient
from app.services.gpt_parse_service import parse_operation_with_gpt


def build_operation_from_text_with_gpt(
    llm: LLMClient,
    text: str,
    tg_user_id: int,
    tg_message_id: int,
    source: str = "text",
) -> Operation:
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")

    parsed = parse_operation_with_gpt(llm=llm, text=text, today=now)

    op_date = parsed["op_date"]  # YYYY-MM-DD
    month_key = op_date[:7] if len(op_date) >= 7 else now.strftime("%Y-%m")

    amount = int(parsed["amount"])
    category = parsed["category"]
    needs_review = bool(parsed["needs_review"])

    if needs_review or not category:
        status = "pending"
        needs_review_str = "TRUE"
        category = ""
    else:
        status = "ok"
        needs_review_str = "FALSE"

    return Operation(
        created_at=created_at,
        op_date=op_date,
        category=category,
        amount=amount,
        comment_raw=text,
        source=source,
        tg_user_id=tg_user_id,
        tg_message_id=tg_message_id,
        status=status,
        needs_review=needs_review_str,
        month_key=month_key,
        error="",
    )
