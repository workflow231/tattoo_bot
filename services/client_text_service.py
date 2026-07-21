from __future__ import annotations

import json
from pathlib import Path
from string import Formatter
from typing import Any

TELEGRAM_MESSAGE_LIMIT = 4096
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "client_texts.json"

DEFAULT_TEXTS = {
    "welcome_new_user": "Добро пожаловать!",
    "welcome_existing_user": "С возвращением!",
    "master_contact": "Связаться с мастером:\n\n{contact}",
    "master_contact_missing": (
        "Контакт мастера пока не указан.\n\n"
        "Попробуйте написать позже или дождитесь ответа по заявке."
    ),
    "appointment_created": (
        "Заявка создана и ожидает подтверждения.\n\n"
        "После разговора с мастером админ подтвердит или отклонит заявку."
    ),
    "appointment_confirmed": (
        "Ваша заявка подтверждена.\n\n"
        "Дата: {appointment_date}\n"
        "Время: {appointment_time}\n"
        "Эскиз: {sketch_name}\n\n"
        "За день до записи бот пришлёт напоминание."
    ),
    "appointment_rejected": (
        "Ваша заявка отклонена.\n\n"
        "Свяжитесь с мастером, чтобы выбрать другую дату или уточнить детали."
    ),
    "reminder_tomorrow": (
        "Напоминание о записи\n\n"
        "Завтра у вас сеанс тату.\n\n"
        "Дата: {appointment_date}\n"
        "Время: {appointment_time}\n"
        "Эскиз: {sketch_name}\n\n"
        "Если планы изменились — напишите мастеру заранее."
    ),
    "stale_session": "Сессия устарела. Откройте нужный раздел заново.",
    "my_socials": "Соц сети еще не добавленны",
    "main_menu": "Главное меню",
    "choose_action": "Выберите действие кнопкой.",
    "booking_menu_prompt": "Выберите вариант записи:",
    "custom_sketch_menu_prompt": (
        "Вы можете отправить свой эскиз или написать мастеру."
    ),
    "custom_sketch_photo_prompt": "Отправьте фото вашего эскиза.",
    "custom_sketch_photo_required": "Отправьте фото эскиза, чтобы продолжить.",
    "appointment_choose_date": (
        "Выберите дату: {month_title}\n\n" "Недоступные дни отмечены символом ×."
    ),
    "appointment_choose_available_day": "Выберите доступный день в календаре.",
    "appointment_no_slots_for_date": (
        "На эту дату нет свободных слотов. Выберите другую дату."
    ),
    "appointment_date_unavailable": ("Этот день недоступен. Выберите другую дату."),
    "appointment_date_in_past": "Эта дата уже прошла. Выберите другую дату.",
    "appointment_temporary_day_off": (
        "В этот день у мастера выходной. Выберите другую дату."
    ),
    "appointment_weekly_day_off": (
        "Этот день недели отмечен как выходной. Выберите другую дату."
    ),
    "appointment_choose_time": "Выберите время:",
    "appointment_choose_time_button": "Выберите время кнопкой из списка.",
    "appointment_comment_prompt": (
        "Оставьте комментарий к заявке или нажмите «Пропустить»."
    ),
    "appointment_cancelled": "Создание заявки отменено.",
    "appointment_create_missing_data": (
        "Не удалось создать заявку. Попробуйте заново."
    ),
    "appointment_create_failed": (
        "Не удалось создать заявку. Возможно, эскиз недоступен или слот уже занят."
    ),
    "appointment_missing_data": "Не хватает данных для заявки. Выберите дату заново.",
    "appointment_sketch_missing": "Сначала выберите эскиз из каталога.",
    "appointment_sketch_unavailable": "Эскиз не найден или уже недоступен.",
    "appointment_summary": (
        "Проверьте заявку:\n\n"
        "Эскиз: {sketch_name}\n"
        "Дата: {appointment_date}\n"
        "Время: {appointment_time}\n"
        "Комментарий: {comment}\n\n"
        "Статус после создания: ждёт подтверждения"
    ),
    "appointment_card": (
        "Заявка #{appointment_id}\n\n"
        "Эскиз: {sketch_name}\n"
        "Дата: {appointment_date}\n"
        "Время: {appointment_time}\n"
        "Статус: {status}\n"
        "Комментарий: {comment}"
    ),
    "appointment_list_item": (
        "#{appointment_id} — {appointment_date} {appointment_time} — {status}"
    ),
    "appointment_back_to_sketch_card": "Вы вернулись к карточке эскиза.",
    "appointments_choose_from_list": "Выберите заявку кнопкой из списка.",
    "appointments_empty": "У вас пока нет заявок.",
    "appointments_list": "Ваши заявки:\n\n{appointments}",
    "appointment_not_found": "Заявка не найдена.",
    "appointment_not_selected": "Заявка не выбрана.",
    "user_unknown": "Не удалось определить пользователя.",
    "appointment_user_cancelled": "Заявка отменена.",
    "appointment_cancel_confirmed_not_allowed": (
        "Подтверждённую заявку нельзя отменить в боте. Напишите мастеру."
    ),
    "appointment_cancel_unavailable": "Эту заявку уже нельзя отменить.",
    "catalog_empty": (
        "К сожалению, список стилей пока пуст, но он обязательно скоро появится."
    ),
    "catalog_empty_short": "К сожалению, список стилей пока пуст.",
    "catalog_choose_style_button": "Выберите стиль кнопкой из списка.",
    "catalog_style_empty": "В этом стиле пока нет доступных эскизов.",
    "catalog_choose_sketch_button": "Выберите эскиз кнопкой из списка.",
    "catalog_sketch_unavailable": "Эскиз не найден или уже недоступен.",
    "catalog_return_failed": (
        "Не удалось вернуться к списку эскизов. Откройте каталог заново."
    ),
    "catalog_open_failed": (
        "Не удалось открыть список эскизов. Откройте каталог заново."
    ),
    "catalog_choose_style_title": "Выберите стиль",
    "catalog_choose_sketch_title": "Выберите эскиз",
    "catalog_page_title": "{title}: страница {page} из {pages}",
    "client_calendar_opened": "Календарь мастера открыт.",
    "client_calendar_use_inline_buttons": "Используйте inline-кнопки календаря.",
    "client_calendar_no_slots": "На эту дату свободных слотов нет.",
    "client_calendar_day_slots": (
        "{appointment_date}\n\n"
        "Свободные слоты:\n"
        "{available_times}\n\n"
        "Запись создаётся через меню записи."
    ),
    "client_calendar_month": (
        "Календарь мастера: {month_title}\n\n"
        "Можно посмотреть свободные слоты.\n"
        "Запись создаётся через меню записи."
    ),
}


class ClientTextService:
    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._texts = self._load_texts()

    def welcome_new_user(self) -> str:
        return self._get_text("welcome_new_user")

    def welcome_existing_user(self) -> str:
        return self._get_text("welcome_existing_user")

    def master_contact(self, contact: str) -> str:
        return self._format_text(
            name="master_contact",
            contact=contact,
        )

    def master_contact_missing(self) -> str:
        return self._get_text("master_contact_missing")

    def appointment_created(self) -> str:
        return self._get_text("appointment_created")

    def appointment_confirmed(
        self,
        appointment_date: str,
        appointment_time: str,
        sketch_name: str,
    ) -> str:
        return self._format_text(
            name="appointment_confirmed",
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            sketch_name=sketch_name,
        )

    def appointment_rejected(self) -> str:
        return self._get_text("appointment_rejected")

    def reminder_tomorrow(
        self,
        appointment_date: str,
        appointment_time: str,
        sketch_name: str,
    ) -> str:
        return self._format_text(
            name="reminder_tomorrow",
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            sketch_name=sketch_name,
        )

    def stale_session(self) -> str:
        return self._get_text("stale_session")

    def my_socials(self) -> str:
        return self._get_text("my_socials")

    def text(self, name: str) -> str:
        return self._get_text(name)

    def format_text(self, name: str, **values: Any) -> str:
        return self._format_text(name=name, **values)

    def _format_text(self, name: str, **values: Any) -> str:
        default = DEFAULT_TEXTS[name]
        template = self._get_raw_text(name=name) or default
        rendered = self._safe_format(template=template, values=values)

        if not rendered:
            rendered = self._safe_format(template=default, values=values)

        if not rendered or len(rendered) > TELEGRAM_MESSAGE_LIMIT:
            fallback = self._safe_format(template=default, values=values) or default
            return self._limit_text(fallback)

        return rendered

    def _get_text(self, name: str) -> str:
        default = DEFAULT_TEXTS[name]
        text = self._get_raw_text(name=name) or default

        if len(text) > TELEGRAM_MESSAGE_LIMIT:
            return default

        return text

    def _limit_text(self, text: str) -> str:
        if len(text) <= TELEGRAM_MESSAGE_LIMIT:
            return text

        return text[:TELEGRAM_MESSAGE_LIMIT]

    def _get_raw_text(self, name: str) -> str | None:
        value = self._texts.get(name)

        if not isinstance(value, str) or not value.strip():
            return None

        return value.strip()

    def _load_texts(self) -> dict[str, str]:
        try:
            raw_data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(raw_data, dict):
            return {}

        return {key: value for key, value in raw_data.items() if isinstance(value, str)}

    def _safe_format(self, template: str, values: dict[str, Any]) -> str | None:
        try:
            self._validate_placeholders(template=template, values=values)
            return template.format(**values)
        except (KeyError, ValueError, IndexError):
            return None

    def _validate_placeholders(self, template: str, values: dict[str, Any]) -> None:
        for _, field_name, _, _ in Formatter().parse(template):
            if field_name and field_name not in values:
                raise KeyError(field_name)
