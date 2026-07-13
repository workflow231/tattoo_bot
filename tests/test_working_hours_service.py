from datetime import date, time

import pytest

from db.models import (
    ScheduleException,
    TemporaryWorkingHours,
    WeeklyDayOff,
    WeeklyWorkingHours,
)
from services.working_hours_service import WorkingHoursService
from services.working_hours_service import WorkingHoursDraft


def test_build_time_texts_includes_end_time() -> None:
    service = WorkingHoursService(session=None)
    working_hours = WeeklyWorkingHours(
        weekday=4,
        start_time=time(10, 0),
        end_time=time(18, 0),
        slot_step_minutes=120,
    )

    assert service.build_time_texts(working_hours) == [
        "10:00",
        "12:00",
        "14:00",
        "16:00",
        "18:00",
    ]


def test_build_draft_rejects_invalid_interval() -> None:
    service = WorkingHoursService(session=None)

    assert (
        service.build_draft(
            start_time=time(18, 0),
            end_time=time(10, 0),
            slot_step_minutes=120,
        )
        is None
    )


def test_build_draft_rejects_step_outside_interval() -> None:
    service = WorkingHoursService(session=None)

    assert (
        service.build_draft(
            start_time=time(10, 0),
            end_time=time(11, 0),
            slot_step_minutes=120,
        )
        is None
    )


def test_parse_weekday() -> None:
    service = WorkingHoursService(session=None)

    assert service.parse_weekday("Пятница") == 4
    assert service.parse_weekday("Нет такого дня") is None


@pytest.mark.anyio
async def test_get_rules_text_lists_all_rule_types(monkeypatch) -> None:
    async def fake_list_weekly_day_offs(session):
        return [WeeklyDayOff(weekday=6)]

    async def fake_list_weekly_working_hours(session):
        return [
            WeeklyWorkingHours(
                weekday=4,
                start_time=time(10, 0),
                end_time=time(18, 0),
                slot_step_minutes=120,
            )
        ]

    async def fake_list_temporary_day_offs(session, start_date, end_date):
        return [
            ScheduleException(
                date=date(2026, 7, 14),
                time_slot=None,
                type="temporary_day_off",
            )
        ]

    async def fake_list_temporary_working_hours(session):
        return [
            TemporaryWorkingHours(
                date=date(2026, 7, 15),
                start_time=time(12, 0),
                end_time=time(16, 0),
                slot_step_minutes=60,
            )
        ]

    monkeypatch.setattr(
        "services.working_hours_service.list_weekly_day_offs",
        fake_list_weekly_day_offs,
    )
    monkeypatch.setattr(
        "services.working_hours_service.list_weekly_working_hours",
        fake_list_weekly_working_hours,
    )
    monkeypatch.setattr(
        "services.working_hours_service.list_temporary_day_offs",
        fake_list_temporary_day_offs,
    )
    monkeypatch.setattr(
        "services.working_hours_service.list_temporary_working_hours",
        fake_list_temporary_working_hours,
    )

    result = await WorkingHoursService(session=None).get_rules_text()

    assert "Постоянные выходные:\nВоскресенье" in result
    assert "Пятница: 10:00-18:00, шаг 120 мин." in result
    assert "14.07.2026" in result
    assert "15.07.2026: 12:00-16:00, шаг 60 мин." in result
    assert "Без рабочих часов день закрыт." in result


@pytest.mark.anyio
async def test_get_time_texts_for_date_returns_empty_without_working_hours(
    monkeypatch,
) -> None:
    async def fake_is_day_off(self, day):
        return False

    async def fake_find_temporary_working_hours(session, day):
        return None

    async def fake_find_weekly_working_hours(session, weekday):
        return None

    monkeypatch.setattr(WorkingHoursService, "is_day_off", fake_is_day_off)
    monkeypatch.setattr(
        "services.working_hours_service.find_temporary_working_hours",
        fake_find_temporary_working_hours,
    )
    monkeypatch.setattr(
        "services.working_hours_service.find_weekly_working_hours",
        fake_find_weekly_working_hours,
    )

    result = await WorkingHoursService(session=None).get_time_texts_for_date(
        date(2026, 7, 17),
    )

    assert result == []


@pytest.mark.anyio
async def test_get_day_rule_text_reports_closed_without_working_hours(
    monkeypatch,
) -> None:
    async def fake_is_day_off(self, day):
        return False

    async def fake_find_temporary_working_hours(session, day):
        return None

    async def fake_find_weekly_working_hours(session, weekday):
        return None

    monkeypatch.setattr(WorkingHoursService, "is_day_off", fake_is_day_off)
    monkeypatch.setattr(
        "services.working_hours_service.find_temporary_working_hours",
        fake_find_temporary_working_hours,
    )
    monkeypatch.setattr(
        "services.working_hours_service.find_weekly_working_hours",
        fake_find_weekly_working_hours,
    )

    result = await WorkingHoursService(session=None).get_day_rule_text(
        date(2026, 7, 17),
    )

    assert result == "Рабочие часы: не заданы, день закрыт."


@pytest.mark.anyio
async def test_remove_weekly_working_hours_returns_success_text(monkeypatch) -> None:
    async def fake_remove_weekly_working_hours(session, weekday):
        return True

    monkeypatch.setattr(
        "services.working_hours_service.remove_weekly_working_hours",
        fake_remove_weekly_working_hours,
    )

    result = await WorkingHoursService(session=None).remove_weekly_working_hours(
        weekday=4,
    )

    assert result == "Постоянные рабочие часы на пятница сняты."


@pytest.mark.anyio
async def test_set_weekly_working_hours_removes_weekly_day_off(monkeypatch) -> None:
    calls = []

    async def fake_remove_weekly_day_off(session, weekday):
        calls.append(("remove_day_off", weekday))
        return True

    async def fake_upsert_weekly_working_hours(
        session,
        weekday,
        start_time,
        end_time,
        slot_step_minutes,
    ):
        calls.append(("upsert_hours", weekday))

    monkeypatch.setattr(
        "services.working_hours_service.remove_weekly_day_off",
        fake_remove_weekly_day_off,
    )
    monkeypatch.setattr(
        "services.working_hours_service.upsert_weekly_working_hours",
        fake_upsert_weekly_working_hours,
    )

    await WorkingHoursService(session=None).set_weekly_working_hours(
        weekday=0,
        draft=WorkingHoursDraft(
            start_time=time(10, 0),
            end_time=time(18, 0),
            slot_step_minutes=60,
        ),
    )

    assert calls == [("remove_day_off", 0), ("upsert_hours", 0)]


@pytest.mark.anyio
async def test_add_weekly_day_off_removes_weekly_working_hours(monkeypatch) -> None:
    calls = []

    async def fake_remove_weekly_working_hours(session, weekday):
        calls.append(("remove_hours", weekday))
        return True

    async def fake_add_weekly_day_off(session, weekday):
        calls.append(("add_day_off", weekday))

    monkeypatch.setattr(
        "services.working_hours_service.remove_weekly_working_hours",
        fake_remove_weekly_working_hours,
    )
    monkeypatch.setattr(
        "services.working_hours_service.add_weekly_day_off",
        fake_add_weekly_day_off,
    )

    await WorkingHoursService(session=None).add_weekly_day_off(weekday=0)

    assert calls == [("remove_hours", 0), ("add_day_off", 0)]


@pytest.mark.anyio
async def test_remove_temporary_working_hours_handles_missing_rule(monkeypatch) -> None:
    async def fake_remove_temporary_working_hours(session, day):
        return False

    monkeypatch.setattr(
        "services.working_hours_service.remove_temporary_working_hours",
        fake_remove_temporary_working_hours,
    )

    result = await WorkingHoursService(session=None).remove_temporary_working_hours(
        day=date(2026, 7, 13),
    )

    assert result == "Временные рабочие часы для этой даты не найдены."
