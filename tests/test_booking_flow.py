import pytest

from bot.handlers import appointments
from bot.keyboards import (
    BACK_BUTTON,
    CHOOSE_SKETCH_BUTTON,
    MAIN_MENU_BUTTON,
    NO_SKETCH_REQUEST_BUTTON,
    build_booking_menu_keyboard,
    build_custom_sketch_menu_keyboard,
    master_menu_kb,
)
from bot.states import AppointmentState, BookingState


class FakeUser:
    def __init__(self, user_id: int = 123):
        self.id = user_id


class FakePhoto:
    def __init__(self, file_id: str):
        self.file_id = file_id


class FakeState:
    def __init__(self):
        self.clear_called = False
        self.current_state = None
        self.data = {}

    async def clear(self):
        self.clear_called = True
        self.data = {}

    async def set_state(self, state):
        self.current_state = state

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def get_data(self):
        return self.data


class FakeMessage:
    def __init__(self, text: str | None, user_id: int = 123, photo=None):
        self.text = text
        self.from_user = FakeUser(user_id)
        self.photo = photo or []
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.anyio
async def test_booking_main_menu_returns_admin_keyboard(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    state = FakeState()
    message = FakeMessage(MAIN_MENU_BUTTON, user_id=123)

    await appointments.choose_booking_action(
        message=message,
        state=state,
        session=None,
    )

    assert state.clear_called is True
    assert message.answers == [("Главное меню", master_menu_kb)]


@pytest.mark.anyio
async def test_booking_back_returns_admin_keyboard(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    state = FakeState()
    message = FakeMessage(BACK_BUTTON, user_id=123)

    await appointments.choose_booking_action(
        message=message,
        state=state,
        session=None,
    )

    assert state.clear_called is True
    assert message.answers == [("Главное меню", master_menu_kb)]


@pytest.mark.anyio
async def test_choose_sketch_opens_existing_catalog(monkeypatch) -> None:
    called = {}

    async def fake_start_sketch_catalog(message, state, session):
        called["message"] = message
        called["state"] = state
        called["session"] = session

    monkeypatch.setattr(
        "bot.handlers.appointments.start_sketch_catalog",
        fake_start_sketch_catalog,
    )

    state = FakeState()
    message = FakeMessage(CHOOSE_SKETCH_BUTTON)

    await appointments.choose_booking_action(
        message=message,
        state=state,
        session="session",
    )

    assert called == {"message": message, "state": state, "session": "session"}


@pytest.mark.anyio
async def test_no_sketch_booking_starts_appointment_date_selection(monkeypatch) -> None:
    async def fake_send_calendar(session, message, state, target_date):
        state.data["calendar_sent"] = True

    monkeypatch.setattr(
        "bot.handlers.appointments._send_appointment_calendar",
        fake_send_calendar,
    )

    state = FakeState()
    message = FakeMessage(NO_SKETCH_REQUEST_BUTTON)

    await appointments.choose_booking_action(
        message=message,
        state=state,
        session=None,
    )

    assert state.current_state == AppointmentState.choosing_date
    assert state.data["appointment_request_type"] == "no_sketch"
    assert state.data["sketch_id"] is None
    assert state.data["calendar_sent"] is True


@pytest.mark.anyio
async def test_custom_sketch_rejects_non_photo() -> None:
    state = FakeState()
    message = FakeMessage(text="not a photo")

    await appointments.collect_custom_sketch_photo(
        message=message,
        state=state,
        session=None,
    )

    assert message.answers == [
        (
            "Отправьте фото эскиза, чтобы продолжить.",
            build_custom_sketch_menu_keyboard(),
        )
    ]


@pytest.mark.anyio
async def test_custom_sketch_photo_starts_appointment_date_selection(
    monkeypatch,
) -> None:
    async def fake_send_calendar(session, message, state, target_date):
        state.data["calendar_sent"] = True

    monkeypatch.setattr(
        "bot.handlers.appointments._send_appointment_calendar",
        fake_send_calendar,
    )

    state = FakeState()
    message = FakeMessage(text=None, photo=[FakePhoto("small"), FakePhoto("large")])

    await appointments.collect_custom_sketch_photo(
        message=message,
        state=state,
        session=None,
    )

    assert state.current_state == AppointmentState.choosing_date
    assert state.data["appointment_request_type"] == "custom_sketch"
    assert state.data["client_sketch_photo_file_id"] == "large"
    assert state.data["calendar_sent"] is True


@pytest.mark.anyio
async def test_show_booking_menu_enters_booking_state() -> None:
    state = FakeState()
    message = FakeMessage("Запись")

    await appointments.show_booking_menu(message=message, state=state)

    assert state.clear_called is True
    assert state.current_state == BookingState.choosing_action
    assert message.answers == [
        ("Выберите вариант записи:", build_booking_menu_keyboard())
    ]
