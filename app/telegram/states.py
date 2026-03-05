from aiogram.fsm.state import State, StatesGroup


class EditJournalStates(StatesGroup):
    selecting_row = State()        # Пользователь выбирает запись из списка
    choosing_action = State()      # Пользователь выбирает действие редактирования
    waiting_amount = State()       # Ввод суммы
    waiting_date = State()         # Ввод даты
    choosing_category = State()    # Выбор категории через клавиатуру
    confirming_cancel = State()    # Подтверждение отмены


class FeedbackStates(StatesGroup):
    waiting_text = State()  # Ждём описание ошибки от пользователя


class CategoryEditStates(StatesGroup):
    waiting_selection = State()  # Пользователь выбирает категорию
    waiting_action = State()     # Пользователь видит возможные действия
    waiting_name = State()       # Ждём новое имя для категории или имя новой категории
    confirm_delete = State()     # Подтверждение удаления категории
