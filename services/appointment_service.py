from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment, Sketch, User
from db.repositories.appointment_repo import (
    change_appointment_status,
    create_appointment,
    find_user_appointment_by_id,
    list_confirmed_times_for_date,
    list_user_appointments,
)
from db.repositories.schedule_repo import (
    find_temporary_day_off,
    find_weekly_day_off,
    list_blocked_slots_for_day,
)
from db.repositories.sketch_repo import get_sketch_by_id_with_style
from db.repositories.user_repo import get_user_by_telegram_id
from utils.appointment_slots import DEFAULT_APPOINTMENT_TIMES
from utils.admin_calendar import MONTH_NAMES, shift_month

DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"


@dataclass(frozen=True)
class AppointmentDraft:
    sketch_id: int
    appointment_date: date
    appointment_time: time
    comment: str | None


@dataclass(frozen=True)
class AppointmentListItem:
    id: int
    text: str


@dataclass(frozen=True)
class AppointmentCalendarMonth:
    year: int
    month: int
    title: str
    weeks: list[list[str]]
    available_dates: dict[str, str]
    previous_year: int
    previous_month: int
    next_year: int
    next_month: int


@dataclass(frozen=True)
class AppointmentDateAvailability:
    available: bool
    message: str | None = None


class AppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_sketch(self, sketch_id: int) -> Sketch | None:
        return await get_sketch_by_id_with_style(
            session=self.session,
            sketch_id=sketch_id,
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return await get_user_by_telegram_id(
            session=self.session,
            telegram_id=telegram_id,
        )

    async def create_pending_appointment(
        self,
        telegram_id: int,
        draft: AppointmentDraft,
    ) -> Appointment | None:
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)
        sketch = await self.get_sketch(sketch_id=draft.sketch_id)

        if not user or not sketch or sketch.status != "available":
            return None

        slot_is_available = await self.is_time_available(
            appointment_date=draft.appointment_date,
            appointment_time=draft.appointment_time,
        )

        if not slot_is_available:
            return None

        return await create_appointment(
            session=self.session,
            user_id=user.id,
            sketch_id=sketch.id,
            appointment_date=draft.appointment_date,
            appointment_time=draft.appointment_time,
            client_comment=draft.comment,
            status="pending",
        )

    async def get_available_time_texts(
        self,
        appointment_date: date,
    ) -> list[str]:
        if await self.is_date_unavailable(appointment_date=appointment_date):
            return []

        busy_times = await list_confirmed_times_for_date(
            session=self.session,
            appointment_date=appointment_date,
        )
        busy_time_texts = {busy_time.strftime(TIME_FORMAT) for busy_time in busy_times}
        blocked_time_texts = await self.get_blocked_time_texts(
            appointment_date=appointment_date,
        )

        return [
            time_text
            for time_text in DEFAULT_APPOINTMENT_TIMES
            if time_text not in busy_time_texts and time_text not in blocked_time_texts
        ]

    async def is_date_unavailable(self, appointment_date: date) -> bool:
        temporary_day_off = await find_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )
        weekly_day_off = await find_weekly_day_off(
            session=self.session,
            weekday=appointment_date.weekday(),
        )
        return temporary_day_off is not None or weekly_day_off is not None

    async def get_blocked_time_texts(self, appointment_date: date) -> set[str]:
        blocked_slots = await list_blocked_slots_for_day(
            session=self.session,
            day=appointment_date,
        )
        return {
            blocked_slot.time_slot.strftime(TIME_FORMAT)
            for blocked_slot in blocked_slots
            if blocked_slot.time_slot
        }

    async def get_date_availability(
        self,
        appointment_date: date,
    ) -> AppointmentDateAvailability:
        if appointment_date < date.today():
            return AppointmentDateAvailability(
                available=False,
                message="Эта дата уже прошла. Выберите другую дату.",
            )

        temporary_day_off = await find_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )

        if temporary_day_off:
            return AppointmentDateAvailability(
                available=False,
                message="В этот день у мастера выходной. Выберите другую дату.",
            )

        weekly_day_off = await find_weekly_day_off(
            session=self.session,
            weekday=appointment_date.weekday(),
        )

        if weekly_day_off:
            return AppointmentDateAvailability(
                available=False,
                message="Этот день недели отмечен как выходной. Выберите другую дату.",
            )

        available_times = await self.get_available_time_texts(
            appointment_date=appointment_date,
        )

        if not available_times:
            return AppointmentDateAvailability(
                available=False,
                message="На эту дату нет свободных слотов. Выберите другую дату.",
            )

        return AppointmentDateAvailability(available=True)

    async def is_time_available(
        self,
        appointment_date: date,
        appointment_time: time,
    ) -> bool:
        available_time_texts = await self.get_available_time_texts(
            appointment_date=appointment_date,
        )
        return appointment_time.strftime(TIME_FORMAT) in available_time_texts

    async def get_calendar_month(
        self,
        year: int,
        month: int,
    ) -> AppointmentCalendarMonth:
        _, last_day = monthrange(year, month)
        available_dates = {}
        weeks = []
        week = []
        previous_year, previous_month = shift_month(year=year, month=month, step=-1)
        next_year, next_month = shift_month(year=year, month=month, step=1)

        for day_number in range(1, last_day + 1):
            current_date = date(year, month, day_number)
            label = str(day_number)

            if current_date < date.today():
                label = f"{label} ×"
            else:
                available_times = await self.get_available_time_texts(
                    appointment_date=current_date,
                )

                if available_times:
                    available_dates[label] = current_date.isoformat()
                else:
                    label = f"{label} ×"

            week.append(label)

            if len(week) == 7:
                weeks.append(week)
                week = []

        if week:
            weeks.append(week)

        return AppointmentCalendarMonth(
            year=year,
            month=month,
            title=f"{MONTH_NAMES[month - 1]} {year}",
            weeks=weeks,
            available_dates=available_dates,
            previous_year=previous_year,
            previous_month=previous_month,
            next_year=next_year,
            next_month=next_month,
        )

    @staticmethod
    def shift_month(year: int, month: int, step: int) -> tuple[int, int]:
        return shift_month(year=year, month=month, step=step)

    async def list_current_user_appointments(
        self,
        telegram_id: int,
    ) -> list[AppointmentListItem]:
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)

        if not user:
            return []

        appointments = await list_user_appointments(
            session=self.session,
            user_id=user.id,
        )

        return [
            AppointmentListItem(
                id=appointment.id,
                text=self.build_list_item_text(appointment),
            )
            for appointment in appointments
        ]

    async def get_current_user_appointment_card(
        self,
        telegram_id: int,
        appointment_id: int,
    ) -> str | None:
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)

        if not user:
            return None

        appointment = await find_user_appointment_by_id(
            session=self.session,
            user_id=user.id,
            appointment_id=appointment_id,
        )

        if not appointment:
            return None

        return self.build_appointment_card_text(appointment)

    async def can_cancel_current_user_appointment(
        self,
        telegram_id: int,
        appointment_id: int,
    ) -> bool:
        appointment = await self.get_current_user_appointment(
            telegram_id=telegram_id,
            appointment_id=appointment_id,
        )
        return appointment is not None and appointment.status == "pending"

    async def cancel_current_user_appointment(
        self,
        telegram_id: int,
        appointment_id: int,
    ) -> str | None:
        appointment = await self.get_current_user_appointment(
            telegram_id=telegram_id,
            appointment_id=appointment_id,
        )

        if not appointment:
            return None

        if appointment.status == "confirmed":
            return "Подтверждённую заявку нельзя отменить в боте. Напишите мастеру."

        if appointment.status != "pending":
            return "Эту заявку уже нельзя отменить."

        cancelled_appointment = await change_appointment_status(
            session=self.session,
            appointment_id=appointment.id,
            status="cancelled",
        )

        if not cancelled_appointment:
            return None

        return "Заявка отменена."

    async def get_current_user_appointment(
        self,
        telegram_id: int,
        appointment_id: int,
    ) -> Appointment | None:
        user = await self.get_user_by_telegram_id(telegram_id=telegram_id)

        if not user:
            return None

        return await find_user_appointment_by_id(
            session=self.session,
            user_id=user.id,
            appointment_id=appointment_id,
        )

    def parse_date(self, value: str) -> date | None:
        try:
            parsed_date = datetime.strptime(value.strip(), DATE_FORMAT).date()
        except ValueError:
            return None

        if parsed_date < date.today():
            return None

        return parsed_date

    def parse_time(self, value: str) -> time | None:
        try:
            return datetime.strptime(value.strip(), TIME_FORMAT).time()
        except ValueError:
            return None

    def build_summary_text(
        self,
        sketch: Sketch,
        draft: AppointmentDraft,
    ) -> str:
        comment = draft.comment or "Не указан"

        return (
            "Проверьте заявку:\n\n"
            f"Эскиз: {sketch.name}\n"
            f"Дата: {draft.appointment_date.strftime(DATE_FORMAT)}\n"
            f"Время: {draft.appointment_time.strftime(TIME_FORMAT)}\n"
            f"Комментарий: {comment}\n\n"
            "Статус после создания: ждёт подтверждения"
        )

    def build_list_item_text(self, appointment: Appointment) -> str:
        return (
            f"#{appointment.id} — "
            f"{appointment.appointment_date.strftime(DATE_FORMAT)} "
            f"{appointment.appointment_time.strftime(TIME_FORMAT)} — "
            f"{self.format_status(appointment.status)}"
        )

    def build_appointment_card_text(self, appointment: Appointment) -> str:
        sketch_name = appointment.sketch.name if appointment.sketch else "Не указан"
        comment = appointment.client_comment or "Не указан"

        return (
            f"Заявка #{appointment.id}\n\n"
            f"Эскиз: {sketch_name}\n"
            f"Дата: {appointment.appointment_date.strftime(DATE_FORMAT)}\n"
            f"Время: {appointment.appointment_time.strftime(TIME_FORMAT)}\n"
            f"Статус: {self.format_status(appointment.status)}\n"
            f"Комментарий: {comment}"
        )

    def format_status(self, status: str) -> str:
        statuses = {
            "pending": "ждёт подтверждения",
            "confirmed": "подтверждена",
            "rejected": "отклонена",
            "cancelled": "отменена",
        }

        return statuses.get(status, status)
