from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import bot.handlers.admin_appointments as admin_appointments
import bot.handlers.appointments as appointments_handler
from bot.handlers.admin_appointments import _send_admin_appointments_list
from bot.handlers.appointments import _send_my_appointments_list
from bot.keyboards import NEXT_PAGE_BUTTON, PREVIOUS_PAGE_BUTTON


@dataclass(frozen=True)
class ListItem:
    id: int
    text: str


class FakeState:
    def __init__(self):
        self.data = {}
        self.state = None

    async def clear(self):
        self.data.clear()
        self.state = None

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.state = state


class FakeMessage:
    def __init__(self, user_id: int = 123):
        self.from_user = SimpleNamespace(id=user_id)
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.anyio
async def test_client_appointments_list_shows_first_page_only(monkeypatch) -> None:
    monkeypatch.setattr(
        appointments_handler,
        "AppointmentService",
        _fake_client_service(_items(12)),
    )
    state = FakeState()
    message = FakeMessage()

    await _send_my_appointments_list(session=None, message=message, state=state)

    text, keyboard = message.answers[0]
    button_texts = _keyboard_texts(keyboard)

    assert "Заявка 10" in text
    assert "Заявка 11" not in text
    assert "Заявка #10" in button_texts
    assert "Заявка #11" not in button_texts
    assert NEXT_PAGE_BUTTON in button_texts
    assert PREVIOUS_PAGE_BUTTON not in button_texts
    assert state.data["appointment_buttons"] == {
        f"Заявка #{index}": index for index in range(1, 11)
    }
    assert state.data["appointment_page"] == 0
    assert state.data["appointment_count"] == 12


@pytest.mark.anyio
async def test_client_appointments_list_shows_second_page(monkeypatch) -> None:
    monkeypatch.setattr(
        appointments_handler,
        "AppointmentService",
        _fake_client_service(_items(12)),
    )
    state = FakeState()
    message = FakeMessage()

    await _send_my_appointments_list(
        session=None,
        message=message,
        state=state,
        page=1,
    )

    text, keyboard = message.answers[0]
    button_texts = _keyboard_texts(keyboard)

    assert "Заявка 11" in text
    assert "Заявка 12" in text
    assert "Заявка 10" not in text
    assert "Заявка #11" in button_texts
    assert "Заявка #12" in button_texts
    assert NEXT_PAGE_BUTTON not in button_texts
    assert PREVIOUS_PAGE_BUTTON in button_texts
    assert state.data["appointment_buttons"] == {
        "Заявка #11": 11,
        "Заявка #12": 12,
    }
    assert state.data["appointment_page"] == 1


@pytest.mark.anyio
async def test_admin_appointments_list_shows_first_page_only(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_appointments,
        "AdminAppointmentService",
        _fake_admin_service(_items(12)),
    )
    state = FakeState()
    message = FakeMessage()

    await _send_admin_appointments_list(
        session=None,
        message=message,
        state=state,
        filter_text="Все заявки",
    )

    text, keyboard = message.answers[0]
    button_texts = _keyboard_texts(keyboard)

    assert "Заявка 10" in text
    assert "Заявка 11" not in text
    assert "Открыть #10" in button_texts
    assert "Открыть #11" not in button_texts
    assert NEXT_PAGE_BUTTON in button_texts
    assert PREVIOUS_PAGE_BUTTON not in button_texts
    assert state.data["admin_appointment_buttons"] == {
        f"Открыть #{index}": index for index in range(1, 11)
    }
    assert state.data["admin_appointment_filter"] == "Все заявки"
    assert state.data["admin_appointment_page"] == 0
    assert state.data["admin_appointment_count"] == 12


@pytest.mark.anyio
async def test_admin_appointments_list_shows_second_page(monkeypatch) -> None:
    monkeypatch.setattr(
        admin_appointments,
        "AdminAppointmentService",
        _fake_admin_service(_items(12)),
    )
    state = FakeState()
    message = FakeMessage()

    await _send_admin_appointments_list(
        session=None,
        message=message,
        state=state,
        filter_text="Все заявки",
        page=1,
    )

    text, keyboard = message.answers[0]
    button_texts = _keyboard_texts(keyboard)

    assert "Заявка 11" in text
    assert "Заявка 12" in text
    assert "Заявка 10" not in text
    assert "Открыть #11" in button_texts
    assert "Открыть #12" in button_texts
    assert NEXT_PAGE_BUTTON not in button_texts
    assert PREVIOUS_PAGE_BUTTON in button_texts
    assert state.data["admin_appointment_buttons"] == {
        "Открыть #11": 11,
        "Открыть #12": 12,
    }
    assert state.data["admin_appointment_page"] == 1


def _items(count: int) -> list[ListItem]:
    return [ListItem(id=index, text=f"Заявка {index}") for index in range(1, count + 1)]


def _fake_client_service(items):
    class FakeAppointmentService:
        def __init__(self, session):
            self.session = session

        async def list_current_user_appointments(self, telegram_id: int):
            return items

    return FakeAppointmentService


def _fake_admin_service(items):
    class FakeAdminAppointmentService:
        def __init__(self, session):
            self.session = session

        async def list_appointments_by_filter(self, filter_text: str):
            return items

        def build_admin_list_title(self, filter_text: str) -> str:
            return f"{filter_text}:"

    return FakeAdminAppointmentService


def _keyboard_texts(keyboard) -> list[str]:
    return [button.text for row in keyboard.keyboard for button in row]
