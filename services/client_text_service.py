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

    def _format_text(self, name: str, **values: Any) -> str:
        default = DEFAULT_TEXTS[name]
        template = self._get_raw_text(name=name) or default
        rendered = self._safe_format(template=template, values=values)

        if not rendered:
            rendered = self._safe_format(template=default, values=values)

        if not rendered or len(rendered) > TELEGRAM_MESSAGE_LIMIT:
            return self._safe_format(template=default, values=values) or default

        return rendered

    def _get_text(self, name: str) -> str:
        default = DEFAULT_TEXTS[name]
        text = self._get_raw_text(name=name) or default

        if len(text) > TELEGRAM_MESSAGE_LIMIT:
            return default

        return text

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
