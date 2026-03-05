import unittest

from app.sheets.category_repo import Category
from app.telegram.handlers import edit_choose_action
from app.telegram.states import EditJournalStates


class _FakeState:
    def __init__(self, row_index: int = 10):
        self._data = {"row_index": row_index}
        self.last_state = None
        self.cleared = False

    async def get_data(self):
        return self._data

    async def set_state(self, state):
        self.last_state = state

    async def clear(self):
        self.cleared = True


class _FakeMessage:
    def __init__(self):
        self.calls = []

    async def edit_text(self, text, reply_markup=None):
        self.calls.append({"text": text, "reply_markup": reply_markup})


class _FakeCallback:
    def __init__(self, data: str):
        self.data = data
        self.message = _FakeMessage()
        self.answer_calls = []

    async def answer(self, text=None, show_alert=False):
        self.answer_calls.append({"text": text, "show_alert": show_alert})


class _FakeCategoryRepo:
    def list_active(self):
        return [
            Category(
                category_id="must_products",
                name="Продукты",
                section="must",
                order=10,
                is_active=True,
            )
        ]


class _FakeJournalRepo:
    pass


class EditChooseActionStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_amount_sets_waiting_amount(self):
        callback = _FakeCallback("edit:action:amount")
        state = _FakeState()

        await edit_choose_action(callback, state, _FakeJournalRepo(), _FakeCategoryRepo())

        self.assertEqual(state.last_state, EditJournalStates.waiting_amount)
        self.assertEqual(callback.message.calls[-1]["text"], "Введите новую сумму числом:")

    async def test_date_sets_waiting_date(self):
        callback = _FakeCallback("edit:action:date")
        state = _FakeState()

        await edit_choose_action(callback, state, _FakeJournalRepo(), _FakeCategoryRepo())

        self.assertEqual(state.last_state, EditJournalStates.waiting_date)
        self.assertIn("Введите новую дату", callback.message.calls[-1]["text"])

    async def test_category_sets_choosing_category(self):
        callback = _FakeCallback("edit:action:category")
        state = _FakeState()

        await edit_choose_action(callback, state, _FakeJournalRepo(), _FakeCategoryRepo())

        self.assertEqual(state.last_state, EditJournalStates.choosing_category)
        self.assertEqual(callback.message.calls[-1]["text"], "Выберите новую категорию:")
        self.assertIsNotNone(callback.message.calls[-1]["reply_markup"])

    async def test_cancel_sets_confirming_cancel(self):
        callback = _FakeCallback("edit:action:cancel")
        state = _FakeState()

        await edit_choose_action(callback, state, _FakeJournalRepo(), _FakeCategoryRepo())

        self.assertEqual(state.last_state, EditJournalStates.confirming_cancel)
        self.assertIn("Вы уверены, что хотите отменить запись?", callback.message.calls[-1]["text"])

    async def test_unknown_action_keeps_state_and_alerts(self):
        callback = _FakeCallback("edit:action:unknown")
        state = _FakeState()

        await edit_choose_action(callback, state, _FakeJournalRepo(), _FakeCategoryRepo())

        self.assertIsNone(state.last_state)
        self.assertEqual(len(callback.answer_calls), 1)
        self.assertEqual(callback.answer_calls[0]["text"], "Неизвестное действие")
        self.assertTrue(callback.answer_calls[0]["show_alert"])


if __name__ == "__main__":
    unittest.main()
