from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.models import Style, Sketch


BACK_BUTTON = "⬅️ Назад"
MAIN_MENU_BUTTON = "🏠 Главное меню"

CREATE_REQUEST_BUTTON = "📝 Создать заявку"
LEAVE_COMMENT_BUTTON = "💬 Оставить комментарий"
CHAT_WITH_MASTER_BUTTON = "👨‍🎨 Чат с мастером"


def build_styles_reply_keyboard(styles: list[Style]) -> ReplyKeyboardMarkup:
    keyboard = []

    row = []
    for style in styles:
        row.append(KeyboardButton(text=style.name))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text=MAIN_MENU_BUTTON)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_sketches_reply_keyboard(sketches: list[Sketch]) -> ReplyKeyboardMarkup:
    keyboard = []

    for sketch in sketches:
        price = f" — от {sketch.price} ₽" if sketch.price else " — цена договорная"

        keyboard.append([
            KeyboardButton(text=f"{sketch.name}{price}")
        ])

    keyboard.append([
        KeyboardButton(text=BACK_BUTTON),
        KeyboardButton(text=MAIN_MENU_BUTTON),
    ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


sketch_card_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=CREATE_REQUEST_BUTTON)],
        [KeyboardButton(text=LEAVE_COMMENT_BUTTON)],
        [KeyboardButton(text=CHAT_WITH_MASTER_BUTTON)],
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ],
    ],
    resize_keyboard=True,
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Каталог эскизов"),
            KeyboardButton(text="Календарь с записями"),
        ],
        [
            KeyboardButton(text="Мои заявки"),
            KeyboardButton(text="Чат с продавцом"),
        ],
    ],
    resize_keyboard=True,
)
