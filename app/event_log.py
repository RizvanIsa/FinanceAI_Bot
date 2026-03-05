from __future__ import annotations

import logging
import os

EVENT_LOG_PATH = "logs/bot_events.log"
_LOGGER_NAME = "finbot.events"


def setup_event_log(log_path: str = EVENT_LOG_PATH) -> None:
    """
    Настраивает логирование событий в отдельный файл.
    При старте файл очищается (режим 'w').
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_event(message: str) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.info(message)


def clear_event_log(log_path: str = EVENT_LOG_PATH) -> None:
    """
    Полностью очищает файл логов при остановке бота.
    """
    try:
        if os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8"):
                pass
    except Exception:
        pass
