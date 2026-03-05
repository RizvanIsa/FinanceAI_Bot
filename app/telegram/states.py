from aiogram.fsm.state import State, StatesGroup


class EditJournalStates(StatesGroup):
    selecting_row = State()        # РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ РІС‹Р±РёСЂР°РµС‚ Р·Р°РїРёСЃСЊ РёР· СЃРїРёСЃРєР°
    choosing_action = State()      # РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ РІС‹Р±РёСЂР°РµС‚, С‡С‚Рѕ РјРµРЅСЏС‚СЊ
    waiting_amount = State()       # Р¶РґРµРј РІРІРѕРґР° СЃСѓРјРјС‹ С‚РµРєСЃС‚РѕРј
    waiting_date = State()         # Р¶РґРµРј РІРІРѕРґР° РґР°С‚С‹ С‚РµРєС‚РѕРј
    choosing_category = State()    # Р¶РґРµРј РІС‹Р±РѕСЂ РєР°С‚РµРіРѕСЂРёРё РєРЅРѕРїРєРѕР№ (РєР°Рє pending)
    confirming_cancel = State()    # РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ РѕС‚РјРµРЅС‹


class FeedbackStates(StatesGroup):
    waiting_text = State()  # РїРѕР»СѓС‡Р°РµРј РѕРїРёСЃР°РЅРёРµ РѕС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
