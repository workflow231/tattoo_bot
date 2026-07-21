from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TemporaryWorkingHours, WeeklyWorkingHours
from db.repositories.schedule_repo import (
    add_temporary_day_off,
    add_weekly_day_off,
    find_temporary_day_off,
    find_temporary_working_hours,
    find_weekly_day_off,
    find_weekly_working_hours,
    list_temporary_day_offs,
    list_temporary_working_hours,
    list_weekly_day_offs,
    list_weekly_working_hours,
    remove_temporary_day_off,
    remove_temporary_working_hours,
    remove_weekly_day_off,
    remove_weekly_working_hours,
    upsert_temporary_working_hours,
    upsert_weekly_working_hours,
)
from utils.admin_calendar import format_weekday_name

DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"
TIME_CALCULATION_DATE = date(2000, 1, 1)

WEEKDAY_BUTTONS = {
    "Понедельник": 0,
    "Вторник": 1,
    "Среда": 2,
    "Четверг": 3,
    "Пятница": 4,
    "Суббота": 5,
    "Воскресенье": 6,
}


@dataclass(frozen=True)
class WorkingHoursDraft:
    start_time: time
    end_time: time
    slot_step_minutes: int


class WorkingHoursService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_weekly_day_off(self, weekday: int) -> str:
        await remove_weekly_working_hours(session=self.session, weekday=weekday)
        await add_weekly_day_off(session=self.session, weekday=weekday)
        return f"{format_weekday_name(weekday)} добавлен как постоянный выходной."

    async def add_temporary_day_off(self, day: date) -> str:
        await remove_temporary_working_hours(session=self.session, day=day)
        await add_temporary_day_off(session=self.session, day=day)
        return f"{day.strftime(DATE_FORMAT)} отмечен как временный выходной."

    async def set_weekly_working_hours(
        self,
        weekday: int,
        draft: WorkingHoursDraft,
    ) -> str:
        await remove_weekly_day_off(session=self.session, weekday=weekday)
        await upsert_weekly_working_hours(
            session=self.session,
            weekday=weekday,
            start_time=draft.start_time,
            end_time=draft.end_time,
            slot_step_minutes=draft.slot_step_minutes,
        )
        return (
            f"Рабочие часы на {format_weekday_name(weekday).lower()} сохранены:\n"
            f"{self.format_draft(draft)}"
        )

    async def set_temporary_working_hours(
        self,
        day: date,
        draft: WorkingHoursDraft,
    ) -> str:
        await remove_temporary_day_off(session=self.session, day=day)
        await upsert_temporary_working_hours(
            session=self.session,
            day=day,
            start_time=draft.start_time,
            end_time=draft.end_time,
            slot_step_minutes=draft.slot_step_minutes,
        )
        return (
            f"Временные рабочие часы на {day.strftime(DATE_FORMAT)} сохранены:\n"
            f"{self.format_draft(draft)}"
        )

    async def remove_weekly_working_hours(self, weekday: int) -> str:
        removed = await remove_weekly_working_hours(
            session=self.session,
            weekday=weekday,
        )

        if not removed:
            return "Постоянные рабочие часы для этого дня недели не найдены."

        return (
            f"Постоянные рабочие часы на {format_weekday_name(weekday).lower()} сняты."
        )

    async def remove_temporary_working_hours(self, day: date) -> str:
        removed = await remove_temporary_working_hours(
            session=self.session,
            day=day,
        )

        if not removed:
            return "Временные рабочие часы для этой даты не найдены."

        return f"Временные рабочие часы на {day.strftime(DATE_FORMAT)} сняты."

    async def get_rules_text(self) -> str:
        weekly_day_offs = await list_weekly_day_offs(session=self.session)
        weekly_working_hours = await list_weekly_working_hours(session=self.session)
        temporary_day_offs = await list_temporary_day_offs(
            session=self.session,
            start_date=date.min,
            end_date=date.max,
        )
        temporary_working_hours = await list_temporary_working_hours(
            session=self.session,
        )
        lines = ["Правила рабочего времени:"]

        lines.extend(
            [
                "",
                "Постоянные выходные:",
                self._format_weekday_list(
                    weekly_day_off.weekday for weekly_day_off in weekly_day_offs
                ),
            ]
        )
        lines.extend(["", "Постоянные рабочие часы:"])
        lines.extend(
            self._format_weekly_working_hours_list(
                working_hours=weekly_working_hours,
            )
        )
        lines.extend(["", "Временные выходные:"])
        lines.extend(self._format_temporary_day_off_list(day_offs=temporary_day_offs))
        lines.extend(["", "Временные рабочие часы:"])
        lines.extend(
            self._format_temporary_working_hours_list(
                working_hours=temporary_working_hours,
            )
        )
        lines.extend(
            [
                "",
                "Приоритет: выходной > временные часы > постоянные часы. "
                "Без рабочих часов день закрыт.",
            ]
        )

        return "\n".join(lines)

    async def get_time_texts_for_date(self, day: date) -> list[str]:
        if await self.is_day_off(day=day):
            return []

        temporary_hours = await find_temporary_working_hours(
            session=self.session,
            day=day,
        )

        if temporary_hours:
            return self.build_time_texts(temporary_hours)

        weekly_hours = await find_weekly_working_hours(
            session=self.session,
            weekday=day.weekday(),
        )

        if weekly_hours:
            return self.build_time_texts(weekly_hours)

        return []

    async def get_day_rule_text(self, day: date) -> str:
        if await self.is_day_off(day=day):
            return "Рабочие часы: день отмечен как выходной."

        temporary_hours = await find_temporary_working_hours(
            session=self.session,
            day=day,
        )

        if temporary_hours:
            return (
                "Рабочие часы: временное правило, "
                f"{self.format_working_hours(temporary_hours)}."
            )

        weekly_hours = await find_weekly_working_hours(
            session=self.session,
            weekday=day.weekday(),
        )

        if weekly_hours:
            return (
                "Рабочие часы: постоянное правило, "
                f"{self.format_working_hours(weekly_hours)}."
            )

        return "Рабочие часы: не заданы, день закрыт."

    async def is_day_off(self, day: date) -> bool:
        temporary_day_off = await find_temporary_day_off(
            session=self.session,
            day=day,
        )
        weekly_day_off = await find_weekly_day_off(
            session=self.session,
            weekday=day.weekday(),
        )
        return temporary_day_off is not None or weekly_day_off is not None

    def parse_weekday(self, value: str | None) -> int | None:
        return WEEKDAY_BUTTONS.get((value or "").strip())

    def parse_date(self, value: str | None) -> date | None:
        try:
            return datetime.strptime((value or "").strip(), DATE_FORMAT).date()
        except ValueError:
            return None

    def parse_time(self, value: str | None) -> time | None:
        try:
            return datetime.strptime((value or "").strip(), TIME_FORMAT).time()
        except ValueError:
            return None

    def parse_slot_step(self, value: str | None) -> int | None:
        value = (value or "").strip()

        if not value.isdigit():
            return None

        slot_step_minutes = int(value)

        if slot_step_minutes <= 0:
            return None

        return slot_step_minutes

    def build_draft(
        self,
        start_time: time,
        end_time: time,
        slot_step_minutes: int,
    ) -> WorkingHoursDraft | None:
        if start_time >= end_time:
            return None

        duration_minutes = self._minutes_between(
            start_time=start_time,
            end_time=end_time,
        )

        if slot_step_minutes > duration_minutes:
            return None

        return WorkingHoursDraft(
            start_time=start_time,
            end_time=end_time,
            slot_step_minutes=slot_step_minutes,
        )

    def build_time_texts(
        self,
        working_hours: WeeklyWorkingHours | TemporaryWorkingHours,
    ) -> list[str]:
        result = []
        current_dt = datetime.combine(TIME_CALCULATION_DATE, working_hours.start_time)
        end_dt = datetime.combine(TIME_CALCULATION_DATE, working_hours.end_time)
        step = timedelta(minutes=working_hours.slot_step_minutes)

        while current_dt <= end_dt:
            result.append(current_dt.time().strftime(TIME_FORMAT))
            current_dt += step

        return result

    def format_draft(self, draft: WorkingHoursDraft) -> str:
        return (
            f"{draft.start_time.strftime(TIME_FORMAT)}-"
            f"{draft.end_time.strftime(TIME_FORMAT)}, "
            f"шаг {draft.slot_step_minutes} мин."
        )

    def format_working_hours(
        self,
        working_hours: WeeklyWorkingHours | TemporaryWorkingHours,
    ) -> str:
        return (
            f"{working_hours.start_time.strftime(TIME_FORMAT)}-"
            f"{working_hours.end_time.strftime(TIME_FORMAT)}, "
            f"шаг {working_hours.slot_step_minutes} мин."
        )

    def _format_weekday_list(self, weekdays) -> str:
        weekday_names = [format_weekday_name(weekday) for weekday in weekdays]

        if not weekday_names:
            return "Не заданы."

        return ", ".join(weekday_names)

    def _format_weekly_working_hours_list(
        self,
        working_hours: list[WeeklyWorkingHours],
    ) -> list[str]:
        if not working_hours:
            return ["Не заданы."]

        return [
            f"{format_weekday_name(item.weekday)}: {self.format_working_hours(item)}"
            for item in working_hours
        ]

    def _format_temporary_day_off_list(self, day_offs) -> list[str]:
        if not day_offs:
            return ["Не заданы."]

        return [day_off.date.strftime(DATE_FORMAT) for day_off in day_offs]

    def _format_temporary_working_hours_list(
        self,
        working_hours: list[TemporaryWorkingHours],
    ) -> list[str]:
        if not working_hours:
            return ["Не заданы."]

        return [
            f"{item.date.strftime(DATE_FORMAT)}: {self.format_working_hours(item)}"
            for item in working_hours
        ]

    def _minutes_between(self, start_time: time, end_time: time) -> int:
        start_dt = datetime.combine(TIME_CALCULATION_DATE, start_time)
        end_dt = datetime.combine(TIME_CALCULATION_DATE, end_time)
        return int((end_dt - start_dt).total_seconds() // 60)
