from types import SimpleNamespace

import pytest

import bot.handlers.admin_calendar as admin_calendar
import bot.handlers.client_calendar as client_calendar
from bot.handlers.admin_calendar import handle_admin_calendar_callback
from bot.handlers.client_calendar import handle_client_calendar_callback
from services.client_text_service import ClientTextService


class FakeState:
    async def get_data(self):
        return {}


class FakeMessage:
    def __init__(self):
        self.answers = []
        self.edits = []

    async def answer(self, text: str, **kwargs):
        self.answers.append((text, kwargs))

    async def edit_text(self, text: str, **kwargs):
        self.edits.append((text, kwargs))


class FakeCallback:
    def __init__(self, data: str, user_id: int = 123):
        self.data = data
        self.message = FakeMessage()
        self.from_user = SimpleNamespace(id=user_id)
        self.answers = []

    async def answer(self, text: str | None = None, show_alert: bool | None = None):
        self.answers.append((text, show_alert))


@pytest.mark.anyio
async def test_client_calendar_rejects_invalid_month_callback(monkeypatch) -> None:
    async def fail_edit_month(**kwargs):
        raise AssertionError("month callback should not reach calendar service")

    monkeypatch.setattr(client_calendar, "_edit_client_calendar_month", fail_edit_month)
    callback = FakeCallback("clical:month:not-a-year:7")

    await handle_client_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [(ClientTextService().stale_session(), True)]


@pytest.mark.anyio
async def test_client_calendar_rejects_invalid_day_callback(monkeypatch) -> None:
    class FailingAppointmentService:
        def __init__(self, session):
            self.session = session

        async def get_date_availability(self, appointment_date):
            raise AssertionError("day callback should not reach appointment service")

    monkeypatch.setattr(
        client_calendar,
        "AppointmentService",
        FailingAppointmentService,
    )
    callback = FakeCallback("clical:day:not-a-date")

    await handle_client_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [(ClientTextService().stale_session(), True)]


@pytest.mark.anyio
async def test_client_calendar_rejects_malformed_month_callback() -> None:
    callback = FakeCallback("clical:month:2026")

    await handle_client_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [(ClientTextService().stale_session(), True)]


@pytest.mark.anyio
async def test_admin_calendar_rejects_invalid_month_callback(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")

    async def fail_edit_month(**kwargs):
        raise AssertionError("month callback should not reach calendar service")

    monkeypatch.setattr(admin_calendar, "_edit_admin_calendar_month", fail_edit_month)
    callback = FakeCallback("admcal:month:2026:not-a-month")

    await handle_admin_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [
        (admin_calendar.STALE_ADMIN_CALENDAR_TEXT, True),
    ]


@pytest.mark.anyio
async def test_admin_calendar_rejects_invalid_day_callback(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")

    async def fail_edit_day(**kwargs):
        raise AssertionError("day callback should not reach calendar service")

    monkeypatch.setattr(admin_calendar, "_edit_admin_calendar_day", fail_edit_day)
    callback = FakeCallback("admcal:day:not-a-date")

    await handle_admin_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [
        (admin_calendar.STALE_ADMIN_CALENDAR_TEXT, True),
    ]


@pytest.mark.anyio
async def test_admin_calendar_rejects_malformed_appointment_callback(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    callback = FakeCallback("admcal:appointment")

    await handle_admin_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [
        (admin_calendar.STALE_ADMIN_CALENDAR_TEXT, True),
    ]


@pytest.mark.anyio
async def test_admin_calendar_rejects_invalid_appointment_id_callback(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")

    async def fail_edit_appointment(**kwargs):
        raise AssertionError(
            "appointment callback should not reach appointment service"
        )

    monkeypatch.setattr(
        admin_calendar,
        "_edit_admin_calendar_appointment_card",
        fail_edit_appointment,
    )
    callback = FakeCallback("admcal:appointment:not-an-id")

    await handle_admin_calendar_callback(
        callback=callback,
        state=FakeState(),
        session=None,
    )

    assert callback.answers == [
        (admin_calendar.STALE_ADMIN_CALENDAR_TEXT, True),
    ]
