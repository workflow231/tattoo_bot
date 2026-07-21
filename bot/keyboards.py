from datetime import date

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from db.models import Style, Sketch

BACK_BUTTON = "⬅️ Назад"
MAIN_MENU_BUTTON = "🏠 Главное меню"
CATALOG_BUTTON = "Запись"

CREATE_REQUEST_BUTTON = "📝 Создать заявку"
CHAT_WITH_MASTER_BUTTON = "👨‍🎨 Чат с мастером"
PREVIOUS_PAGE_BUTTON = "⬅️ Страница"
NEXT_PAGE_BUTTON = "Страница ➡️"
CATALOG_PAGE_SIZE = 10
MY_APPOINTMENTS_BUTTON = "Мои заявки"
CANCEL_APPOINTMENT_BUTTON = "Отменить заявку"
ADMIN_APPOINTMENTS_BUTTON = "Заявки"
ADMIN_SKETCHES_BUTTON = "Эскизы"
ADD_SKETCH_BUTTON = "Добавить эскиз"
DELETE_STYLE_BUTTON = "Удалить стиль"
EDIT_STYLE_BUTTON = "Изменить стиль"
DELETE_SKETCH_BUTTON = "Удалить эскиз"
EDIT_SKETCH_BUTTON = "Изменить эскиз"
CLIENT_CALENDAR_BUTTON = "Календарь"
CALENDAR_BUTTON = "Календарь с записями"
WORKING_HOURS_BUTTON = "Рабочее время"
SHOW_WORKING_HOURS_RULES_BUTTON = "Показать правила"
SET_WEEKLY_DAY_OFF_BUTTON = "Постоянный выходной"
SET_WEEKLY_WORKING_HOURS_BUTTON = "Постоянные рабочие часы"
REMOVE_WEEKLY_WORKING_HOURS_BUTTON = "Снять постоянные рабочие часы"
SET_TEMPORARY_DAY_OFF_BUTTON = "Временный выходной"
SET_TEMPORARY_WORKING_HOURS_BUTTON = "Временные рабочие часы"
REMOVE_TEMPORARY_WORKING_HOURS_BUTTON = "Снять временные рабочие часы"
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
CONFIRM_CREATE_SKETCH_BUTTON = "Сохранить эскиз"
CONFIRM_DELETE_STYLE_BUTTON = "Удалить стиль точно"
CONFIRM_DELETE_SKETCH_BUTTON = "Удалить эскиз точно"
CHANGE_DATE_BUTTON = "Изменить дату"
CHANGE_TIME_BUTTON = "Изменить время"
CHANGE_COMMENT_BUTTON = "Изменить комментарий"
CANCEL_BUTTON = "Отмена"
CREATE_STYLE_BUTTON = "Создать новый стиль"
AVAILABLE_STATUS_BUTTON = "Доступен"
RESERVED_STATUS_BUTTON = "Зарезервирован"
HIDDEN_STATUS_BUTTON = "Скрыт"
EDIT_SKETCH_NAME_BUTTON = "Название"
EDIT_SKETCH_DESCRIPTION_BUTTON = "Описание"
EDIT_SKETCH_PRICE_BUTTON = "Цена"
EDIT_SKETCH_PHOTO_BUTTON = "Фото"
EDIT_SKETCH_STATUS_BUTTON = "Статус"
EDIT_SKETCH_STYLE_BUTTON = "Стиль"

ADMIN_CALENDAR_CALLBACK_PREFIX = "admcal"
CLIENT_CALENDAR_CALLBACK_PREFIX = "clical"
ADMIN_CALENDAR_IGNORE_CALLBACK = f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:ignore"
CLIENT_CALENDAR_IGNORE_CALLBACK = f"{CLIENT_CALENDAR_CALLBACK_PREFIX}:ignore"


def build_back_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_skip_back_main_keyboard() -> ReplyKeyboardMarkup:
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


def build_styles_reply_keyboard(
    styles: list[Style],
    page: int = 0,
    page_size: int = CATALOG_PAGE_SIZE,
) -> ReplyKeyboardMarkup:
    keyboard = []
    page_items = _get_page_items(styles, page=page, page_size=page_size)

    row = []
    for style in page_items:
        row.append(KeyboardButton(text=style.name))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    _append_pagination_row(
        keyboard=keyboard,
        items_count=len(styles),
        page=page,
        page_size=page_size,
    )
    keyboard.append([KeyboardButton(text=MAIN_MENU_BUTTON)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_sketches_reply_keyboard(
    sketches: list[Sketch],
    page: int = 0,
    page_size: int = CATALOG_PAGE_SIZE,
) -> ReplyKeyboardMarkup:
    keyboard = []
    page_items = _get_page_items(sketches, page=page, page_size=page_size)

    for sketch in page_items:
        price = f" — от {sketch.price} ₽" if sketch.price else " — цена договорная"

        keyboard.append([KeyboardButton(text=f"{sketch.name}{price}")])

    _append_pagination_row(
        keyboard=keyboard,
        items_count=len(sketches),
        page=page,
        page_size=page_size,
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


def build_appointment_date_keyboard() -> ReplyKeyboardMarkup:
    return build_back_main_keyboard()


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
    times: list[str] | tuple[str, ...],
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


def build_working_hours_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SHOW_WORKING_HOURS_RULES_BUTTON)],
            [KeyboardButton(text=SET_WEEKLY_DAY_OFF_BUTTON)],
            [KeyboardButton(text=SET_WEEKLY_WORKING_HOURS_BUTTON)],
            [KeyboardButton(text=REMOVE_WEEKLY_WORKING_HOURS_BUTTON)],
            [KeyboardButton(text=SET_TEMPORARY_DAY_OFF_BUTTON)],
            [KeyboardButton(text=SET_TEMPORARY_WORKING_HOURS_BUTTON)],
            [KeyboardButton(text=REMOVE_TEMPORARY_WORKING_HOURS_BUTTON)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_weekday_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Понедельник"),
                KeyboardButton(text="Вторник"),
            ],
            [
                KeyboardButton(text="Среда"),
                KeyboardButton(text="Четверг"),
            ],
            [
                KeyboardButton(text="Пятница"),
                KeyboardButton(text="Суббота"),
            ],
            [KeyboardButton(text="Воскресенье")],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_calendar_keyboard(weeks: list[list[str]]) -> ReplyKeyboardMarkup:
    return build_back_main_keyboard()


def build_admin_calendar_inline_keyboard(
    weeks: list[list[str]],
    year: int,
    month: int,
    previous_year: int,
    previous_month: int,
    next_year: int,
    next_month: int,
) -> InlineKeyboardMarkup:
    keyboard = []

    for week in weeks:
        row = []
        for day_text in week:
            day_number = _extract_day_number(day_text)
            callback_data = ADMIN_CALENDAR_IGNORE_CALLBACK

            if day_number:
                callback_data = (
                    f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:day:"
                    f"{date(year, month, day_number).isoformat()}"
                )

            row.append(
                InlineKeyboardButton(
                    text=day_text,
                    callback_data=callback_data,
                )
            )
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                text=ADMIN_PREVIOUS_MONTH_BUTTON,
                callback_data=(
                    f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:month:"
                    f"{previous_year}:{previous_month}"
                ),
            ),
            InlineKeyboardButton(
                text=ADMIN_NEXT_MONTH_BUTTON,
                callback_data=(
                    f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:month:"
                    f"{next_year}:{next_month}"
                ),
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_client_calendar_inline_keyboard(
    weeks: list[list[str]],
    year: int,
    month: int,
    previous_year: int,
    previous_month: int,
    next_year: int,
    next_month: int,
) -> InlineKeyboardMarkup:
    keyboard = []

    for week in weeks:
        row = []
        for day_text in week:
            day_number = _extract_day_number(day_text)
            callback_data = CLIENT_CALENDAR_IGNORE_CALLBACK

            if day_number:
                callback_data = (
                    f"{CLIENT_CALENDAR_CALLBACK_PREFIX}:day:"
                    f"{date(year, month, day_number).isoformat()}"
                )

            row.append(
                InlineKeyboardButton(
                    text=day_text,
                    callback_data=callback_data,
                )
            )
        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                text=APPOINTMENT_PREVIOUS_MONTH_BUTTON,
                callback_data=(
                    f"{CLIENT_CALENDAR_CALLBACK_PREFIX}:month:"
                    f"{previous_year}:{previous_month}"
                ),
            ),
            InlineKeyboardButton(
                text=APPOINTMENT_NEXT_MONTH_BUTTON,
                callback_data=(
                    f"{CLIENT_CALENDAR_CALLBACK_PREFIX}:month:"
                    f"{next_year}:{next_month}"
                ),
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_admin_calendar_day_inline_keyboard(
    appointments,
    blocked_slot_texts: list[str] | None = None,
    has_temporary_day_off: bool = False,
    has_weekly_day_off: bool = False,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"Открыть #{appointment.id}",
                callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:appointment:{appointment.id}",
            )
        ]
        for appointment in appointments
    ]

    if has_temporary_day_off:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=ADMIN_REMOVE_TEMPORARY_DAY_OFF_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:remove_temp",
                )
            ]
        )

    if has_weekly_day_off:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=ADMIN_REMOVE_WEEKLY_DAY_OFF_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:remove_weekly",
                )
            ]
        )

    for time_text in blocked_slot_texts or []:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{ADMIN_REMOVE_BLOCKED_SLOT_PREFIX} {time_text}",
                    callback_data=(
                        f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:remove_block:"
                        f"{time_text.replace(':', '-')}"
                    ),
                )
            ]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    text=ADMIN_ADD_DAY_OFF_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:add_day_off",
                )
            ],
            [
                InlineKeyboardButton(
                    text=ADMIN_BLOCK_SLOT_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:block_slot",
                )
            ],
            [
                InlineKeyboardButton(
                    text=ADMIN_BACK_TO_CALENDAR_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:back_month",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_admin_day_off_type_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ADMIN_TEMPORARY_DAY_OFF_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:day_off:temporary",
                ),
                InlineKeyboardButton(
                    text=ADMIN_WEEKLY_DAY_OFF_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:day_off:weekly",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ADMIN_BACK_TO_CALENDAR_DAY_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:back_day",
                )
            ],
        ]
    )


def build_admin_slot_inline_keyboard(slot_texts: list[str]) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=time_text,
                callback_data=(
                    f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:block_slot_time:"
                    f"{time_text.replace(':', '-')}"
                ),
            )
        ]
        for time_text in slot_texts
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text=ADMIN_BACK_TO_CALENDAR_DAY_BUTTON,
                callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:back_day",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_admin_calendar_appointment_card_inline_keyboard(
    appointment_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ADMIN_APPROVE_APPOINTMENT_BUTTON,
                    callback_data=(
                        f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:confirm:{appointment_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text=ADMIN_REJECT_APPOINTMENT_BUTTON,
                    callback_data=(
                        f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:reject:{appointment_id}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ADMIN_WRITE_CLIENT_BUTTON,
                    callback_data=(
                        f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:client:{appointment_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ADMIN_BACK_TO_CALENDAR_DAY_BUTTON,
                    callback_data=f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:back_day",
                )
            ],
        ]
    )


def build_admin_sketch_style_keyboard(styles: list[Style]) -> ReplyKeyboardMarkup:
    return build_admin_sketch_style_names_keyboard([style.name for style in styles])


def build_admin_sketch_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADD_SKETCH_BUTTON)],
            [
                KeyboardButton(text=DELETE_STYLE_BUTTON),
                KeyboardButton(text=EDIT_STYLE_BUTTON),
            ],
            [
                KeyboardButton(text=DELETE_SKETCH_BUTTON),
                KeyboardButton(text=EDIT_SKETCH_BUTTON),
            ],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_style_select_keyboard(
    styles: list[Style],
    page: int = 0,
    page_size: int = CATALOG_PAGE_SIZE,
) -> ReplyKeyboardMarkup:
    keyboard = []
    row = []

    for style in _get_page_items(styles, page=page, page_size=page_size):
        row.append(KeyboardButton(text=style.name))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    _append_pagination_row(
        keyboard=keyboard,
        items_count=len(styles),
        page=page,
        page_size=page_size,
    )
    keyboard.append(
        [KeyboardButton(text=BACK_BUTTON), KeyboardButton(text=MAIN_MENU_BUTTON)]
    )

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_admin_sketch_select_keyboard(
    sketches: list[Sketch],
    page: int = 0,
    page_size: int = CATALOG_PAGE_SIZE,
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=format_admin_sketch_button_text(sketch))]
        for sketch in _get_page_items(sketches, page=page, page_size=page_size)
    ]

    _append_pagination_row(
        keyboard=keyboard,
        items_count=len(sketches),
        page=page,
        page_size=page_size,
    )
    keyboard.append(
        [KeyboardButton(text=BACK_BUTTON), KeyboardButton(text=MAIN_MENU_BUTTON)]
    )

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_admin_sketch_edit_fields_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=EDIT_SKETCH_NAME_BUTTON),
                KeyboardButton(text=EDIT_SKETCH_DESCRIPTION_BUTTON),
            ],
            [
                KeyboardButton(text=EDIT_SKETCH_PRICE_BUTTON),
                KeyboardButton(text=EDIT_SKETCH_PHOTO_BUTTON),
            ],
            [
                KeyboardButton(text=EDIT_SKETCH_STATUS_BUTTON),
                KeyboardButton(text=EDIT_SKETCH_STYLE_BUTTON),
            ],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_delete_confirm_keyboard(confirm_button: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=confirm_button)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def format_admin_sketch_button_text(sketch: Sketch) -> str:
    return f"#{sketch.id} {sketch.name}"


def build_admin_sketch_style_names_keyboard(
    style_names: list[str],
) -> ReplyKeyboardMarkup:
    keyboard = []
    row = []

    for style_name in style_names:
        row.append(KeyboardButton(text=style_name))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.extend(
        [
            [KeyboardButton(text=CREATE_STYLE_BUTTON)],
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


def build_admin_sketch_status_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=AVAILABLE_STATUS_BUTTON),
                KeyboardButton(text=RESERVED_STATUS_BUTTON),
            ],
            [KeyboardButton(text=HIDDEN_STATUS_BUTTON)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


def build_admin_sketch_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CONFIRM_CREATE_SKETCH_BUTTON)],
            [
                KeyboardButton(text=BACK_BUTTON),
                KeyboardButton(text=MAIN_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
    )


sketch_card_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=CREATE_REQUEST_BUTTON)],
        [KeyboardButton(text=CHAT_WITH_MASTER_BUTTON)],
        [
            KeyboardButton(text=BACK_BUTTON),
            KeyboardButton(text=MAIN_MENU_BUTTON),
        ],
    ],
    resize_keyboard=True,
)

client_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=CATALOG_BUTTON),
            KeyboardButton(text=CLIENT_CALENDAR_BUTTON),
        ],
        [
            KeyboardButton(text=MY_APPOINTMENTS_BUTTON),
        ],
        [
            KeyboardButton(text=CHAT_WITH_MASTER_BUTTON),
        ],
    ],
    resize_keyboard=True,
)

master_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=CATALOG_BUTTON),
            KeyboardButton(text=CALENDAR_BUTTON),
        ],
        [
            KeyboardButton(text=ADMIN_APPOINTMENTS_BUTTON),
            KeyboardButton(text=ADMIN_SKETCHES_BUTTON),
        ],
        [
            KeyboardButton(text=WORKING_HOURS_BUTTON),
        ],
    ],
    resize_keyboard=True,
)

menu_kb = client_menu_kb


def get_main_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    return master_menu_kb if is_admin else client_menu_kb


def _extract_day_number(day_text: str) -> int | None:
    day_number_text = day_text.split(" ", maxsplit=1)[0].strip()

    if not day_number_text.isdigit():
        return None

    return int(day_number_text)


def _get_page_items(items, page: int, page_size: int):
    start = page * page_size
    return items[start : start + page_size]


def _append_pagination_row(
    keyboard: list,
    items_count: int,
    page: int,
    page_size: int,
) -> None:
    if items_count <= page_size:
        return

    row = []

    if page > 0:
        row.append(KeyboardButton(text=PREVIOUS_PAGE_BUTTON))

    if (page + 1) * page_size < items_count:
        row.append(KeyboardButton(text=NEXT_PAGE_BUTTON))

    if row:
        keyboard.append(row)
