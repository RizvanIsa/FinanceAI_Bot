DEFAULT_TEMPLATE = [
    # income
    {"category_id": "income_salary", "name": "Зарплата", "section": "income", "order": 10, "is_active": True},
    {"category_id": "income_other", "name": "Прочие доходы", "section": "income", "order": 20, "is_active": True},

    # must
    {"category_id": "must_products", "name": "Продукты", "section": "must", "order": 10, "is_active": True},
    {"category_id": "must_housing", "name": "Жилье", "section": "must", "order": 20, "is_active": True},
    {"category_id": "must_transport", "name": "Транспорт", "section": "must", "order": 30, "is_active": True},
    {"category_id": "must_connection", "name": "Связь", "section": "must", "order": 40, "is_active": True},
    {"category_id": "must_medicine", "name": "Медицина", "section": "must", "order": 50, "is_active": True},

    # optional
    {"category_id": "opt_fun", "name": "Развлечения", "section": "optional", "order": 10, "is_active": True},
    {"category_id": "opt_clothes", "name": "Одежда, обувь", "section": "optional", "order": 20, "is_active": True},
    {"category_id": "opt_other", "name": "Другие расходы", "section": "optional", "order": 90, "is_active": True},

    # reserve
    {"category_id": "reserve_pillow", "name": "Финансовая подушка (10%)", "section": "reserve", "order": 10, "is_active": True},
]