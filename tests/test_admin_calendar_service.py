from datetime import date

import pytest

from services.admin_calendar_service import AdminCalendarService
from utils.admin_calendar import (
    build_month_weeks,
    format_weekday_name,
    iter_month_weeks,
    shift_month,
)


def test_build_weeks_adds_appointment_counts() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={
            date(2026, 7, 5): 3,
            date(2026, 7, 15): 1,
        },
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 · 3" in flattened_days
    assert "15 · 1" in flattened_days
    assert "1" in flattened_days


def test_build_weeks_starts_on_monday_without_padding() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={},
    )

    assert weeks[0] == ["1", "2", "3", "4", "5"]
    assert weeks[1] == ["6", "7", "8", "9", "10", "11", "12"]
    assert weeks[-1] == ["27", "28", "29", "30", "31"]
    assert " " not in [day for week in weeks for day in week]


def test_iter_month_weeks_returns_dates_without_neighbor_month_days() -> None:
    weeks = iter_month_weeks(year=2026, month=7)

    assert [day.day for day in weeks[0]] == [1, 2, 3, 4, 5]
    assert [day.weekday() for day in weeks[1]] == [0, 1, 2, 3, 4, 5, 6]
    assert [day.day for day in weeks[-1]] == [27, 28, 29, 30, 31]


def test_build_weeks_marks_day_offs() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={date(2026, 7, 5): 3},
        day_off_dates={date(2026, 7, 5), date(2026, 7, 6)},
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 × · 3" in flattened_days
    assert "6 ×" in flattened_days


def test_build_weeks_marks_blocked_slot_days() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={date(2026, 7, 5): 3},
        blocked_slot_dates={date(2026, 7, 5), date(2026, 7, 6)},
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 • · 3" in flattened_days
    assert "6 •" in flattened_days


def test_shift_month_handles_year_boundaries() -> None:
    assert shift_month(year=2026, month=1, step=-1) == (
        2025,
        12,
    )
    assert shift_month(year=2026, month=12, step=1) == (
        2027,
        1,
    )


def test_format_weekday_name() -> None:
    assert format_weekday_name(6) == "Воскресенье"


@pytest.mark.anyio
async def test_day_text_includes_working_hours_rule(monkeypatch) -> None:
    async def fake_list_appointments_for_day(session, appointment_date):
        return []

    async def fake_find_temporary_day_off(session, day):
        return None

    async def fake_find_weekly_day_off(session, weekday):
        return None

    async def fake_list_blocked_slots_for_day(session, day):
        return []

    async def fake_get_day_rule_text(self, day):
        return "Рабочие часы: постоянное правило, 10:00-18:00, шаг 120 мин."

    monkeypatch.setattr(
        "services.admin_calendar_service.list_appointments_for_day",
        fake_list_appointments_for_day,
    )
    monkeypatch.setattr(
        "services.admin_calendar_service.find_temporary_day_off",
        fake_find_temporary_day_off,
    )
    monkeypatch.setattr(
        "services.admin_calendar_service.find_weekly_day_off",
        fake_find_weekly_day_off,
    )
    monkeypatch.setattr(
        "services.admin_calendar_service.list_blocked_slots_for_day",
        fake_list_blocked_slots_for_day,
    )
    monkeypatch.setattr(
        "services.working_hours_service.WorkingHoursService.get_day_rule_text",
        fake_get_day_rule_text,
    )

    calendar_day = await AdminCalendarService(session=None).get_day(
        appointment_date=date(2026, 7, 17),
    )

    assert "Рабочие часы: постоянное правило" in calendar_day.text


@pytest.mark.anyio
async def test_add_blocked_slot_uses_working_hours_slots(monkeypatch) -> None:
    calls = []

    async def fake_get_time_texts_for_date(self, day):
        return ["11:00", "13:00"]

    async def fake_add_blocked_slot(session, day, time_slot):
        calls.append((day, time_slot))

    monkeypatch.setattr(
        "services.working_hours_service.WorkingHoursService.get_time_texts_for_date",
        fake_get_time_texts_for_date,
    )
    monkeypatch.setattr(
        "services.admin_calendar_service.add_blocked_slot",
        fake_add_blocked_slot,
    )

    result = await AdminCalendarService(session=None).add_blocked_slot(
        appointment_date=date(2026, 7, 17),
        time_text="13:00",
    )

    assert result == "Слот 13:00 на 17.07.2026 заблокирован."
    assert calls[0][0] == date(2026, 7, 17)
    assert calls[0][1].strftime("%H:%M") == "13:00"


@pytest.mark.anyio
async def test_add_blocked_slot_rejects_time_outside_working_hours(monkeypatch) -> None:
    async def fake_get_time_texts_for_date(self, day):
        return ["11:00", "13:00"]

    monkeypatch.setattr(
        "services.working_hours_service.WorkingHoursService.get_time_texts_for_date",
        fake_get_time_texts_for_date,
    )

    result = await AdminCalendarService(session=None).add_blocked_slot(
        appointment_date=date(2026, 7, 17),
        time_text="12:00",
    )

    assert result is None


@pytest.mark.anyio
async def test_remove_blocked_slot_allows_valid_time_outside_current_schedule(
    monkeypatch,
) -> None:
    calls = []

    async def fake_remove_blocked_slot(session, day, time_slot):
        calls.append((day, time_slot))
        return True

    monkeypatch.setattr(
        "services.admin_calendar_service.remove_blocked_slot",
        fake_remove_blocked_slot,
    )

    result = await AdminCalendarService(session=None).remove_blocked_slot(
        appointment_date=date(2026, 7, 17),
        time_text="09:30",
    )

    assert result == "Блокировка слота 09:30 на 17.07.2026 снята."
    assert calls[0][0] == date(2026, 7, 17)
    assert calls[0][1].strftime("%H:%M") == "09:30"
