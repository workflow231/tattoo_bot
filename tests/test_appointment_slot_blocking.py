from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from services.appointment_service import AppointmentDraft, AppointmentService


@pytest.mark.anyio
async def test_available_times_exclude_pending_and_confirmed_slots(monkeypatch) -> None:
    async def fake_is_date_unavailable(self, appointment_date):
        return False

    async def fake_list_busy_times_for_date(session, appointment_date):
        return [time(10, 0), time(14, 0)]

    async def fake_get_blocked_time_texts(self, appointment_date):
        return set()

    async def fake_get_time_texts_for_date(self, day):
        return ["10:00", "12:00", "14:00"]

    monkeypatch.setattr(
        AppointmentService,
        "is_date_unavailable",
        fake_is_date_unavailable,
    )
    monkeypatch.setattr(
        "services.appointment_service.list_busy_times_for_date",
        fake_list_busy_times_for_date,
    )
    monkeypatch.setattr(
        AppointmentService,
        "get_blocked_time_texts",
        fake_get_blocked_time_texts,
    )
    monkeypatch.setattr(
        "services.working_hours_service.WorkingHoursService.get_time_texts_for_date",
        fake_get_time_texts_for_date,
    )

    result = await AppointmentService(session=None).get_available_time_texts(
        appointment_date=date(2026, 7, 13),
    )

    assert result == ["12:00"]


@pytest.mark.anyio
async def test_create_pending_appointment_handles_busy_slot_race(monkeypatch) -> None:
    async def fake_get_user_by_telegram_id(self, telegram_id):
        return _user()

    async def fake_get_sketch(self, sketch_id):
        return _sketch()

    async def fake_is_time_available(self, appointment_date, appointment_time):
        return True

    async def fake_create_appointment(**kwargs):
        raise IntegrityError("statement", {}, Exception("unique"))

    monkeypatch.setattr(
        AppointmentService,
        "get_user_by_telegram_id",
        fake_get_user_by_telegram_id,
    )
    monkeypatch.setattr(AppointmentService, "get_sketch", fake_get_sketch)
    monkeypatch.setattr(
        AppointmentService,
        "is_time_available",
        fake_is_time_available,
    )
    monkeypatch.setattr(
        "services.appointment_service.create_appointment",
        fake_create_appointment,
    )

    result = await AppointmentService(session=None).create_pending_appointment(
        telegram_id=123,
        draft=AppointmentDraft(
            sketch_id=1,
            appointment_date=date(2026, 7, 13),
            appointment_time=time(12, 0),
            comment=None,
        ),
    )

    assert result is None


@pytest.mark.anyio
async def test_client_calendar_month_uses_monday_weeks_without_padding(
    monkeypatch,
) -> None:
    async def fake_get_available_time_texts(self, appointment_date):
        return ["10:00"]

    monkeypatch.setattr(
        AppointmentService,
        "get_available_time_texts",
        fake_get_available_time_texts,
    )

    calendar_month = await AppointmentService(session=None).get_calendar_month(
        year=2026,
        month=7,
    )
    week_days = [
        [day_text.split()[0] for day_text in week] for week in calendar_month.weeks
    ]

    assert week_days[0] == ["1", "2", "3", "4", "5"]
    assert week_days[1] == ["6", "7", "8", "9", "10", "11", "12"]
    assert week_days[-1] == ["27", "28", "29", "30", "31"]


def _user():
    return type("UserStub", (), {"id": 1})()


def _sketch():
    return type("SketchStub", (), {"id": 1, "status": "available"})()
