from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment
from db.repositories.appointment_repo import (
    count_appointments_by_day,
    list_appointments_for_day,
)
from db.repositories.schedule_repo import (
    add_blocked_slot,
    add_weekly_day_off,
    add_temporary_day_off,
    find_temporary_day_off,
    find_weekly_day_off,
    list_blocked_slots_for_day,
    list_blocked_slots,
    list_temporary_day_offs,
    list_weekly_day_offs,
    remove_blocked_slot,
    remove_temporary_day_off,
    remove_weekly_day_off,
)
from services.appointment_service import DATE_FORMAT, TIME_FORMAT, AppointmentService
from services.working_hours_service import WorkingHoursService
from utils.admin_calendar import (
    MONTH_NAMES,
    build_month_weeks,
    format_weekday_name,
    shift_month,
)


@dataclass(frozen=True)
class AdminCalendarMonth:
    year: int
    month: int
    title: str
    weeks: list[list[str]]
    previous_year: int
    previous_month: int
    next_year: int
    next_month: int


@dataclass(frozen=True)
class AdminCalendarDayAppointment:
    id: int
    text: str


@dataclass(frozen=True)
class AdminCalendarDay:
    appointment_date: date
    text: str
    appointments: list[AdminCalendarDayAppointment]
    blocked_slot_texts: list[str]
    has_temporary_day_off: bool
    has_weekly_day_off: bool


class AdminCalendarService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_formatter = AppointmentService(session=session)
        self.working_hours = WorkingHoursService(session=session)

    async def get_month(self, year: int, month: int) -> AdminCalendarMonth:
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        counts_by_day = await count_appointments_by_day(
            session=self.session,
            start_date=start_date,
            end_date=end_date,
        )
        day_off_dates = await self.get_month_day_off_dates(
            start_date=start_date,
            end_date=end_date,
        )
        blocked_slot_dates = await self.get_month_blocked_slot_dates(
            start_date=start_date,
            end_date=end_date,
        )
        previous_year, previous_month = shift_month(year=year, month=month, step=-1)
        next_year, next_month = shift_month(year=year, month=month, step=1)

        return AdminCalendarMonth(
            year=year,
            month=month,
            title=f"{MONTH_NAMES[month - 1]} {year}",
            weeks=build_month_weeks(
                year=year,
                month=month,
                counts_by_day=counts_by_day,
                day_off_dates=day_off_dates,
                blocked_slot_dates=blocked_slot_dates,
            ),
            previous_year=previous_year,
            previous_month=previous_month,
            next_year=next_year,
            next_month=next_month,
        )

    async def get_month_day_off_dates(
        self,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        temporary_day_offs = await list_temporary_day_offs(
            session=self.session,
            start_date=start_date,
            end_date=end_date,
        )
        weekly_day_offs = await list_weekly_day_offs(session=self.session)
        weekly_day_off_weekdays = {
            weekly_day_off.weekday for weekly_day_off in weekly_day_offs
        }
        day_off_dates = {day_off.date for day_off in temporary_day_offs}

        for day_number in range(1, end_date.day + 1):
            current_date = date(start_date.year, start_date.month, day_number)

            if current_date.weekday() in weekly_day_off_weekdays:
                day_off_dates.add(current_date)

        return day_off_dates

    async def get_month_blocked_slot_dates(
        self,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        blocked_slots = await list_blocked_slots(
            session=self.session,
            start_date=start_date,
            end_date=end_date,
        )
        return {blocked_slot.date for blocked_slot in blocked_slots}

    def build_text(self, calendar_month: AdminCalendarMonth) -> str:
        return (
            f"Календарь записей: {calendar_month.title}\n\n"
            "В счетчике учитываются заявки со статусами "
            "«ждёт подтверждения» и «подтверждена».\n"
            "Выходные отмечены символом ×.\n"
            "Дни с заблокированными слотами отмечены символом •."
        )

    async def get_day(self, appointment_date: date) -> AdminCalendarDay:
        appointments = await list_appointments_for_day(
            session=self.session,
            appointment_date=appointment_date,
        )
        temporary_day_off = await find_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )
        weekly_day_off = await find_weekly_day_off(
            session=self.session,
            weekday=appointment_date.weekday(),
        )
        blocked_slots = await list_blocked_slots_for_day(
            session=self.session,
            day=appointment_date,
        )
        working_hours_text = await WorkingHoursService(
            session=self.session,
        ).get_day_rule_text(day=appointment_date)
        blocked_slot_texts = [
            blocked_slot.time_slot.strftime(TIME_FORMAT)
            for blocked_slot in blocked_slots
            if blocked_slot.time_slot
        ]
        appointment_items = [
            AdminCalendarDayAppointment(
                id=appointment.id,
                text=self.build_day_appointment_text(appointment),
            )
            for appointment in appointments
        ]

        lines = [
            appointment_date.strftime(DATE_FORMAT),
            "",
            f"Заявок на день: {len(appointment_items)}",
            working_hours_text,
        ]

        if temporary_day_off:
            lines.extend(["", "Статус: временный выходной"])

        if weekly_day_off:
            lines.extend(
                [
                    "",
                    "Статус: постоянный выходной",
                    f"Причина: {format_weekday_name(appointment_date.weekday())}",
                ]
            )

        if blocked_slot_texts:
            lines.extend(
                [
                    "",
                    "Заблокированные слоты:",
                    *blocked_slot_texts,
                ]
            )

        if appointment_items:
            lines.extend(["", *[appointment.text for appointment in appointment_items]])

        return AdminCalendarDay(
            appointment_date=appointment_date,
            text="\n".join(lines),
            appointments=appointment_items,
            blocked_slot_texts=blocked_slot_texts,
            has_temporary_day_off=temporary_day_off is not None,
            has_weekly_day_off=weekly_day_off is not None,
        )

    @staticmethod
    def shift_month(year: int, month: int, step: int) -> tuple[int, int]:
        return shift_month(year=year, month=month, step=step)

    async def add_temporary_day_off(self, appointment_date: date) -> str:
        await add_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )
        return (
            f"Дата {appointment_date.strftime(DATE_FORMAT)} "
            "отмечена как временный выходной."
        )

    async def add_weekly_day_off(self, appointment_date: date) -> str:
        weekday = appointment_date.weekday()
        await add_weekly_day_off(
            session=self.session,
            weekday=weekday,
        )
        return f"{format_weekday_name(weekday)} добавлен как постоянный выходной."

    async def remove_temporary_day_off(self, appointment_date: date) -> str:
        removed = await remove_temporary_day_off(
            session=self.session,
            day=appointment_date,
        )

        if not removed:
            return "Временный выходной для этой даты не найден."

        return f"Временный выходной {appointment_date.strftime(DATE_FORMAT)} снят."

    async def remove_weekly_day_off(self, appointment_date: date) -> str:
        weekday = appointment_date.weekday()
        removed = await remove_weekly_day_off(
            session=self.session,
            weekday=weekday,
        )

        if not removed:
            return "Постоянный выходной для этого дня недели не найден."

        return f"Постоянный выходной {format_weekday_name(weekday)} снят."

    async def add_blocked_slot(
        self,
        appointment_date: date,
        time_text: str,
    ) -> str | None:
        parsed_time = self.parse_time(time_text)
        available_time_texts = await self.get_blockable_slot_texts(
            appointment_date=appointment_date,
        )

        if not parsed_time or time_text not in available_time_texts:
            return None

        await add_blocked_slot(
            session=self.session,
            day=appointment_date,
            time_slot=parsed_time,
        )
        return (
            f"Слот {time_text} на {appointment_date.strftime(DATE_FORMAT)} "
            "заблокирован."
        )

    async def remove_blocked_slot(
        self,
        appointment_date: date,
        time_text: str,
    ) -> str | None:
        parsed_time = self.parse_time(time_text)

        if not parsed_time:
            return None

        removed = await remove_blocked_slot(
            session=self.session,
            day=appointment_date,
            time_slot=parsed_time,
        )

        if not removed:
            return f"Блокировка слота {time_text} не найдена."

        return (
            f"Блокировка слота {time_text} на "
            f"{appointment_date.strftime(DATE_FORMAT)} снята."
        )

    async def get_blockable_slot_texts(self, appointment_date: date) -> list[str]:
        return await self.working_hours.get_time_texts_for_date(appointment_date)

    def parse_time(self, value: str | None) -> time | None:
        if not value:
            return None

        try:
            return datetime.strptime(value.strip(), TIME_FORMAT).time()
        except ValueError:
            return None

    def parse_day_label(self, value: str | None, year: int, month: int) -> date | None:
        if not value:
            return None

        day_text = value.split(" · ", maxsplit=1)[0].strip()

        if not day_text.isdigit():
            return None

        try:
            return date(year, month, int(day_text))
        except ValueError:
            return None

    def build_day_appointment_text(self, appointment: Appointment) -> str:
        username = self._format_username(appointment)

        return (
            f"#{appointment.id} — "
            f"{appointment.appointment_time.strftime(TIME_FORMAT)} — "
            f"{username} — "
            f"{self.appointment_formatter.format_status(appointment.status)}"
        )

    def _format_username(self, appointment: Appointment) -> str:
        if not appointment.user:
            return "Не указан"

        if appointment.user.username:
            return f"@{appointment.user.username}"

        return str(appointment.user.telegram_id)
