from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment, Sketch, User
from db.repositories.appointment_repo import (
    change_appointment_status,
    create_appointment,
    find_user_appointment_by_id,
    list_busy_times_for_date,
    list_user_appointments,
)
from db.repositories.schedule_repo import (
    find_temporary_day_off,
    find_weekly_day_off,
    list_blocked_slots_for_day,
)
from db.repositories.sketch_repo import get_sketch_by_id_with_style
from db.repositories.user_repo import get_user_by_telegram_id
from services.client_text_service import ClientTextService
from services.working_hours_service import WorkingHoursService
from utils.admin_calendar import MONTH_NAMES, iter_month_weeks, shift_month
from utils.timezone import today_in_bot_timezone

DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"


@dataclass(frozen=True)
class AppointmentDraft:
    sketch_id: int | None
    appointment_date: date
    appointment_time: time
    comment: str | None
    request_type: str = "catalog_sketch"
    client_sketch_photo_file_id: str | None = None


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

        if not user or not self.is_valid_request_type(draft.request_type):
            return None

        sketch_id = draft.sketch_id

        if draft.request_type == "catalog_sketch":
            if not sketch_id:
                return None

            sketch = await self.get_sketch(sketch_id=sketch_id)

            if not sketch or sketch.status != "available":
                return None
        else:
            sketch_id = None

        if (
            draft.request_type == "custom_sketch"
            and not draft.client_sketch_photo_file_id
        ):
            return None

        slot_is_available = await self.is_time_available(
            appointment_date=draft.appointment_date,
            appointment_time=draft.appointment_time,
        )

        if not slot_is_available:
            return None

        try:
            return await create_appointment(
                session=self.session,
                user_id=user.id,
                sketch_id=sketch_id,
                appointment_date=draft.appointment_date,
                appointment_time=draft.appointment_time,
                request_type=draft.request_type,
                client_sketch_photo_file_id=draft.client_sketch_photo_file_id,
                client_comment=draft.comment,
                status="pending",
            )
        except IntegrityError:
            return None

    async def get_available_time_texts(
        self,
        appointment_date: date,
    ) -> list[str]:
        if await self.is_date_unavailable(appointment_date=appointment_date):
            return []

        busy_times = await list_busy_times_for_date(
            session=self.session,
            appointment_date=appointment_date,
        )
        busy_time_texts = {busy_time.strftime(TIME_FORMAT) for busy_time in busy_times}
        blocked_time_texts = await self.get_blocked_time_texts(
            appointment_date=appointment_date,
        )

        time_texts = await WorkingHoursService(
            session=self.session
        ).get_time_texts_for_date(
            day=appointment_date,
        )

        return [
            time_text
            for time_text in time_texts
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
        if appointment_date < today_in_bot_timezone():
            return AppointmentDateAvailability(
                available=False,
                message=ClientTextService().text("appointment_date_in_past"),
            )

        temporary_day_off = await find_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )

        if temporary_day_off:
            return AppointmentDateAvailability(
                available=False,
                message=ClientTextService().text("appointment_temporary_day_off"),
            )

        weekly_day_off = await find_weekly_day_off(
            session=self.session,
            weekday=appointment_date.weekday(),
        )

        if weekly_day_off:
            return AppointmentDateAvailability(
                available=False,
                message=ClientTextService().text("appointment_weekly_day_off"),
            )

        available_times = await self.get_available_time_texts(
            appointment_date=appointment_date,
        )

        if not available_times:
            return AppointmentDateAvailability(
                available=False,
                message=ClientTextService().text("appointment_no_slots_for_date"),
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
        available_dates = {}
        weeks = []
        previous_year, previous_month = shift_month(year=year, month=month, step=-1)
        next_year, next_month = shift_month(year=year, month=month, step=1)

        for month_week in iter_month_weeks(year=year, month=month):
            week = []

            for current_date in month_week:
                label = str(current_date.day)

                if current_date < today_in_bot_timezone():
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
            return ClientTextService().text("appointment_cancel_confirmed_not_allowed")

        if appointment.status != "pending":
            return ClientTextService().text("appointment_cancel_unavailable")

        cancelled_appointment = await change_appointment_status(
            session=self.session,
            appointment_id=appointment.id,
            status="cancelled",
        )

        if not cancelled_appointment:
            return None

        return ClientTextService().text("appointment_user_cancelled")

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

        if parsed_date < today_in_bot_timezone():
            return None

        return parsed_date

    def parse_time(self, value: str) -> time | None:
        try:
            return datetime.strptime(value.strip(), TIME_FORMAT).time()
        except ValueError:
            return None

    def build_summary_text(
        self,
        sketch: Sketch | None,
        draft: AppointmentDraft,
    ) -> str:
        comment = draft.comment or "Не указан"
        sketch_name = self.format_appointment_sketch(
            request_type=draft.request_type,
            sketch_name=sketch.name if sketch else None,
        )

        return ClientTextService().format_text(
            "appointment_summary",
            sketch_name=sketch_name,
            appointment_date=draft.appointment_date.strftime(DATE_FORMAT),
            appointment_time=draft.appointment_time.strftime(TIME_FORMAT),
            comment=comment,
        )

    def build_list_item_text(self, appointment: Appointment) -> str:
        return ClientTextService().format_text(
            "appointment_list_item",
            appointment_id=str(appointment.id),
            appointment_date=appointment.appointment_date.strftime(DATE_FORMAT),
            appointment_time=appointment.appointment_time.strftime(TIME_FORMAT),
            status=self.format_status(appointment.status),
        )

    def build_appointment_card_text(self, appointment: Appointment) -> str:
        sketch_name = self.get_appointment_sketch_name(appointment)
        comment = appointment.client_comment or "Не указан"

        return ClientTextService().format_text(
            "appointment_card",
            appointment_id=str(appointment.id),
            sketch_name=sketch_name,
            appointment_date=appointment.appointment_date.strftime(DATE_FORMAT),
            appointment_time=appointment.appointment_time.strftime(TIME_FORMAT),
            status=self.format_status(appointment.status),
            comment=comment,
        )

    def format_status(self, status: str) -> str:
        statuses = {
            "pending": "ждёт подтверждения",
            "confirmed": "подтверждена",
            "rejected": "отклонена",
            "cancelled": "отменена",
        }

        return statuses.get(status, status)

    def get_appointment_sketch_name(self, appointment: Appointment) -> str:
        return self.format_appointment_sketch(
            request_type=getattr(appointment, "request_type", "catalog_sketch"),
            sketch_name=appointment.sketch.name if appointment.sketch else None,
        )

    @staticmethod
    def format_appointment_sketch(
        request_type: str,
        sketch_name: str | None,
    ) -> str:
        if request_type == "custom_sketch":
            return "Мой эскиз — цена договорная"

        if request_type == "no_sketch":
            return "Без эскиза"

        return sketch_name or "Не указан"

    @staticmethod
    def is_valid_request_type(request_type: str) -> bool:
        return request_type in {"catalog_sketch", "custom_sketch", "no_sketch"}
