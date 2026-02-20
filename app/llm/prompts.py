from app.data.category_templates import DEFAULT_TEMPLATE

# Список "человеческих" имен категорий для GPT (name)
CATEGORIES = [row["name"] for row in DEFAULT_TEMPLATE]