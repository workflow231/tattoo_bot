from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment
from db.repositories.appointment_repo import (
    change_appointment_status,
    exists_confirmed_appointment_for_slot,
    find_appointment_by_id,
    find_appointment_by_status,
    list_appointments,
)
from services.appointment_service import DATE_FORMAT, TIME_FORMAT, AppointmentService
from services.client_text_service import ClientTextService
from utils.config import get_admin_ids_from_env

ADMIN_STATUS_FILTERS = {
    "Ждут подтверждения": "pending",
    "Подтверждённые": "confirmed",
    "Отклонённые": "rejected",
}

ALL_APPOINTMENTS_FILTER = "Все заявки"


@dataclass(frozen=True)
class AdminAppointmentListItem:
    id: int
    text: str


@dataclass(frozen=True)
class AdminAppointmentActionResult:
    status: str
    admin_message: str
    client_chat_id: int | None = None
    client_message: str | None = None


class AdminAppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_formatter = AppointmentService(session=session)

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in get_admin_ids_from_env()

    async def list_appointments_by_filter(
        self,
        filter_text: str,
    ) -> list[AdminAppointmentListItem]:
        status = ADMIN_STATUS_FILTERS.get(filter_text)

        if filter_text == ALL_APPOINTMENTS_FILTER:
            appointments = await list_appointments(session=self.session)
        elif status:
            appointments = await find_appointment_by_status(
                session=self.session,
                status=status,
            )
        else:
            appointments = []

        return [
            AdminAppointmentListItem(
                id=appointment.id,
                text=self.build_admin_list_item_text(appointment),
            )
            for appointment in appointments
        ]

    async def get_appointment_card(self, appointment_id: int) -> str | None:
        appointment = await find_appointment_by_id(
            session=self.session,
            appointment_id=appointment_id,
        )

        if not appointment:
            return None

        return self.build_admin_card_text(appointment)

    async def get_client_contact_text(self, appointment_id: int) -> str | None:
        appointment = await find_appointment_by_id(
            session=self.session,
            appointment_id=appointment_id,
        )

        if not appointment:
            return None

        return self.build_client_contact_text(appointment)

    async def get_client_sketch_photo_file_id(
        self,
        appointment_id: int,
    ) -> str | None:
        appointment = await find_appointment_by_id(
            session=self.session,
            appointment_id=appointment_id,
        )

        if not appointment:
            return None

        return appointment.client_sketch_photo_file_id

    async def confirm_appointment(
        self,
        appointment_id: int,
    ) -> AdminAppointmentActionResult:
        appointment = await find_appointment_by_id(
            session=self.session,
            appointment_id=appointment_id,
        )

        if not appointment:
            return AdminAppointmentActionResult(
                status="not_found",
                admin_message="Заявка не найдена.",
            )

        if appointment.status != "pending":
            return AdminAppointmentActionResult(
                status="invalid_status",
                admin_message="Подтвердить можно только заявку в статусе «ждёт подтверждения».",
            )

        slot_is_busy = await exists_confirmed_appointment_for_slot(
            session=self.session,
            appointment=appointment,
        )

        if slot_is_busy:
            return AdminAppointmentActionResult(
                status="slot_busy",
                admin_message="Этот слот уже занят другой подтверждённой заявкой.",
            )

        try:
            confirmed_appointment = await change_appointment_status(
                session=self.session,
                appointment_id=appointment.id,
                status="confirmed",
            )
        except IntegrityError:
            return AdminAppointmentActionResult(
                status="slot_busy",
                admin_message="Этот слот уже занят другой подтверждённой заявкой.",
            )

        if not confirmed_appointment:
            return AdminAppointmentActionResult(
                status="not_found",
                admin_message="Заявка не найдена.",
            )

        return AdminAppointmentActionResult(
            status="confirmed",
            admin_message="Заявка подтверждена.",
            client_chat_id=self._get_client_chat_id(confirmed_appointment),
            client_message=self.build_confirmed_client_message(confirmed_appointment),
        )

    async def reject_appointment(
        self,
        appointment_id: int,
    ) -> AdminAppointmentActionResult:
        appointment = await find_appointment_by_id(
            session=self.session,
            appointment_id=appointment_id,
        )

        if not appointment:
            return AdminAppointmentActionResult(
                status="not_found",
                admin_message="Заявка не найдена.",
            )

        if appointment.status != "pending":
            return AdminAppointmentActionResult(
                status="invalid_status",
                admin_message="Отклонить можно только заявку в статусе «ждёт подтверждения».",
            )

        rejected_appointment = await change_appointment_status(
            session=self.session,
            appointment_id=appointment.id,
            status="rejected",
        )

        if not rejected_appointment:
            return AdminAppointmentActionResult(
                status="not_found",
                admin_message="Заявка не найдена.",
            )

        return AdminAppointmentActionResult(
            status="rejected",
            admin_message="Заявка отклонена.",
            client_chat_id=self._get_client_chat_id(rejected_appointment),
            client_message=self.build_rejected_client_message(),
        )

    def build_admin_list_title(self, filter_text: str) -> str:
        if filter_text == "Ждут подтверждения":
            return "Заявки ждут подтверждения:"

        return f"{filter_text}:"

    def build_admin_list_item_text(self, appointment: Appointment) -> str:
        username = self._format_username(appointment)

        return (
            f"#{appointment.id} — {username} — "
            f"{appointment.appointment_date.strftime(DATE_FORMAT)} "
            f"{appointment.appointment_time.strftime(TIME_FORMAT)} — "
            f"{self.appointment_formatter.format_status(appointment.status)}"
        )

    def build_admin_card_text(self, appointment: Appointment) -> str:
        username = self._format_username(appointment)
        telegram_id = appointment.user.telegram_id if appointment.user else "Не указан"
        sketch_name = self.appointment_formatter.get_appointment_sketch_name(
            appointment
        )
        comment = appointment.client_comment or "Не указан"

        return (
            f"Заявка #{appointment.id}\n\n"
            f"Клиент: {username}\n"
            f"Telegram ID: {telegram_id}\n\n"
            f"Эскиз: {sketch_name}\n"
            f"Дата: {appointment.appointment_date.strftime(DATE_FORMAT)}\n"
            f"Время: {appointment.appointment_time.strftime(TIME_FORMAT)}\n"
            f"Статус: {self.appointment_formatter.format_status(appointment.status)}\n\n"
            f"Комментарий:\n{comment}"
        )

    def build_confirmed_client_message(self, appointment: Appointment) -> str:
        sketch_name = self.appointment_formatter.get_appointment_sketch_name(
            appointment
        )

        return ClientTextService().appointment_confirmed(
            appointment_date=appointment.appointment_date.strftime(DATE_FORMAT),
            appointment_time=appointment.appointment_time.strftime(TIME_FORMAT),
            sketch_name=sketch_name,
        )

    def build_rejected_client_message(self) -> str:
        return ClientTextService().appointment_rejected()

    def build_client_contact_text(self, appointment: Appointment) -> str:
        if not appointment.user:
            return "Клиент не найден."

        username = appointment.user.username
        telegram_id = appointment.user.telegram_id

        if username:
            return (
                f"Контакт клиента по заявке #{appointment.id}:\n\n"
                f"@{username}\n"
                f"Telegram ID: {telegram_id}"
            )

        return (
            f"Контакт клиента по заявке #{appointment.id}:\n\n"
            f"Username не указан.\n"
            f"Telegram ID: {telegram_id}"
        )

    def _get_client_chat_id(self, appointment: Appointment) -> int | None:
        if not appointment.user:
            return None

        return appointment.user.telegram_id

    def _format_username(self, appointment: Appointment) -> str:
        if not appointment.user:
            return "Не указан"

        if appointment.user.username:
            return f"@{appointment.user.username}"

        return str(appointment.user.telegram_id)
