from aiogram.fsm.state import State, StatesGroup


class EditJournalStates(StatesGroup):
    selecting_row = State()        # пользователь выбирает запись из списка
    choosing_action = State()      # пользователь выбирает, что менять
    waiting_amount = State()       # ждем ввода суммы текстом
    waiting_date = State()         # ждем ввода даты текстом
    choosing_category = State()    # ждем выбор категории кнопкой (как pending)
    confirming_cancel = State()    # подтверждение отмены
