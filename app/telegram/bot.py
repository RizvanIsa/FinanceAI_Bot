from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

def build_bot(token: str) -> Bot:
    """
    Создаем объект Telegram-бота.
    """
    return Bot(token=token)


def build_dispatcher() -> Dispatcher:
    """
    Создаем диспетчер (роутер событий).
    """
    return Dispatcher(storage=MemoryStorage())
