from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.models import Style, Sketch
from utils.appointment_slots import DEFAULT_APPOINTMENT_TIMES

BACK_BUTTON = "⬅️ Назад"
MAIN_MENU_BUTTON = "🏠 Главное меню"

CREATE_REQUEST_BUTTON = "📝 Создать заявку"
LEAVE_COMMENT_BUTTON = "💬 Оставить комментарий"
CHAT_WITH_MASTER_BUTTON = "👨‍🎨 Чат с мастером"
MY_APPOINTMENTS_BUTTON = "Мои заявки"
CANCEL_APPOINTMENT_BUTTON = "Отменить заявку"
ADMIN_APPOINTMENTS_BUTTON = "Заявки"
CALENDAR_BUTTON = "Календарь с записями"
ADMIN_PENDING_APPOINTMENTS_BUTTON = "Ждут подтверждения"
ADMIN_CONFIRMED_APPOINTMENTS_BUTTON = "Подтверждённые"
ADMIN_REJECTED_APPOINTMENTS_BUTTON = "Отклонённые"
ADMIN_ALL_APPOINTMENTS_BUTTON = "Все заявки"
ADMIN_APPROVE_APPOINTMENT_BUTTON = "Подтвердить"
ADMIN_REJECT_APPOINTMENT_BUTTON = "Отклонить"
ADMIN_WRITE_CLIENT_BUTTON = "Написать клиенту"
ADMIN_BACK_TO_APPOINTMENTS_BUTTON = "Назад к заявкам"
ADMIN_PREVIOUS_MONTH_BUTTON = "⬅️ Месяц"
ADMIN_NEXT_MONTH_BUTTON = "Месяц ➡️"
APPOINTMENT_PREVIOUS_MONTH_BUTTON = "⬅️ Месяц"
APPOINTMENT_NEXT_MONTH_BUTTON = "Месяц ➡️"
ADMIN_ADD_DAY_OFF_BUTTON = "Добавить выходной"
ADMIN_BLOCK_SLOT_BUTTON = "Блокировать слот"
ADMIN_BACK_TO_CALENDAR_BUTTON = "Назад к календарю"
ADMIN_BACK_TO_CALENDAR_DAY_BUTTON = "Назад к дню"
ADMIN_TEMPORARY_DAY_OFF_BUTTON = "Временный"
ADMIN_WEEKLY_DAY_OFF_BUTTON = "Постоянный"
ADMIN_REMOVE_TEMPORARY_DAY_OFF_BUTTON = "Снять временный выходной"
ADMIN_REMOVE_WEEKLY_DAY_OFF_BUTTON = "Снять постоянный выходной"
ADMIN_REMOVE_BLOCKED_SLOT_PREFIX = "Снять блокировку"
SKIP_COMMENT_BUTTON = "Пропустить"
CONFIRM_CREATE_REQUEST_BUTTON = "Создать заявку"
CHANGE_DATE_BUTTON = "Изменить дату"
CHANGE_TIME_BUTTON = "Изменить время"
CHANGE_COMMENT_BUTTON = "Изменить комментарий"
CANCEL_BUTTON = "Отмена"


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

        keyboard.append([KeyboardButton(text=f"{sketch.name}{price}")])

    keyboard.append(
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_appointment_date_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_appointment_calendar_keyboard(weeks: list[list[str]]) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=day_text) for day_text in week] for week in weeks]
    keyboard.append(
        [
            KeyboardButton(text=APPOINTMENT_PREVIOUS_MONTH_BUTTON),
            KeyboardButton(text=APPOINTMENT_NEXT_MONTH_BUTTON),
        ]
    )
    keyboard.append(
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_appointment_time_keyboard(
    times: list[str] | tuple[str, ...] = DEFAULT_APPOINTMENT_TIMES,
) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=time_text)] for time_text in times]
    keyboard.append(
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_appointment_comment_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_COMMENT_BUTTON)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_appointment_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONFIRM_CREATE_REQUEST_BUTTON)],
            [
                KeyboardButton(text=CHANGE_DATE_BUTTON),
                KeyboardButton(text=CHANGE_TIME_BUTTON),
            ],
            [KeyboardButton(text=CHANGE_COMMENT_BUTTON)],
            [
                KeyboardButton(text=CANCEL_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_my_appointments_keyboard(appointments) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=f"Заявка #{appointment.id}")]
        for appointment in appointments
    ]
    keyboard.append([KeyboardButton(text=MAIN_MENU_BUTTON)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_my_appointment_card_keyboard(can_cancel: bool = False) -> ReplyKeyboardMarkup:
    keyboard = []

    if can_cancel:
        keyboard.append([KeyboardButton(text=CANCEL_APPOINTMENT_BUTTON)])

    keyboard.extend(
        [
            [KeyboardButton(text=CHAT_WITH_MASTER_BUTTON)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_admin_appointment_filters_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_PENDING_APPOINTMENTS_BUTTON),
                KeyboardButton(text=ADMIN_CONFIRMED_APPOINTMENTS_BUTTON),
            ],
            [
                KeyboardButton(text=ADMIN_REJECTED_APPOINTMENTS_BUTTON),
                KeyboardButton(text=ADMIN_ALL_APPOINTMENTS_BUTTON),
            ],
            [KeyboardButton(text=MAIN_MENU_BUTTON)],
        ],
        resize_keyboard=True,
    )


def build_admin_appointments_keyboard(appointments) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=f"Открыть #{appointment.id}")]
        for appointment in appointments
    ]
    keyboard.append(
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_admin_appointment_card_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_APPROVE_APPOINTMENT_BUTTON),
                KeyboardButton(text=ADMIN_REJECT_APPOINTMENT_BUTTON),
            ],
            [KeyboardButton(text=ADMIN_WRITE_CLIENT_BUTTON)],
            [
                KeyboardButton(text=ADMIN_BACK_TO_APPOINTMENTS_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_calendar_keyboard(weeks: list[list[str]]) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=day_text) for day_text in week] for week in weeks]
    keyboard.append(
        [
            KeyboardButton(text=ADMIN_PREVIOUS_MONTH_BUTTON),
            KeyboardButton(text=ADMIN_NEXT_MONTH_BUTTON),
        ]
    )
    keyboard.append([KeyboardButton(text=MAIN_MENU_BUTTON)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_admin_calendar_day_keyboard(
    appointments,
    blocked_slot_texts: list[str] | None = None,
    has_temporary_day_off: bool = False,
    has_weekly_day_off: bool = False,
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=f"Открыть #{appointment.id}")]
        for appointment in appointments
    ]

    if has_temporary_day_off:
        keyboard.append([KeyboardButton(text=ADMIN_REMOVE_TEMPORARY_DAY_OFF_BUTTON)])

    if has_weekly_day_off:
        keyboard.append([KeyboardButton(text=ADMIN_REMOVE_WEEKLY_DAY_OFF_BUTTON)])

    for time_text in blocked_slot_texts or []:
        keyboard.append(
            [KeyboardButton(text=f"{ADMIN_REMOVE_BLOCKED_SLOT_PREFIX} {time_text}")]
        )

    keyboard.extend(
        [
            [KeyboardButton(text=ADMIN_ADD_DAY_OFF_BUTTON)],
            [KeyboardButton(text=ADMIN_BLOCK_SLOT_BUTTON)],
            [
                KeyboardButton(text=ADMIN_BACK_TO_CALENDAR_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_admin_day_off_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_TEMPORARY_DAY_OFF_BUTTON),
                KeyboardButton(text=ADMIN_WEEKLY_DAY_OFF_BUTTON),
            ],
            [
                KeyboardButton(text=CANCEL_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_slot_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=time_text)] for time_text in DEFAULT_APPOINTMENT_TIMES
    ]
    keyboard.append(
        [
            KeyboardButton(text=CANCEL_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_admin_calendar_appointment_card_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_APPROVE_APPOINTMENT_BUTTON),
                KeyboardButton(text=ADMIN_REJECT_APPOINTMENT_BUTTON),
            ],
            [KeyboardButton(text=ADMIN_WRITE_CLIENT_BUTTON)],
            [
                KeyboardButton(text=ADMIN_BACK_TO_CALENDAR_DAY_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
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
            KeyboardButton(text=CALENDAR_BUTTON),
        ],
        [
            KeyboardButton(text=MY_APPOINTMENTS_BUTTON),
            KeyboardButton(text=ADMIN_APPOINTMENTS_BUTTON),
        ],
        [
            KeyboardButton(text=CHAT_WITH_MASTER_BUTTON),
        ],
    ],
    resize_keyboard=True,
)
