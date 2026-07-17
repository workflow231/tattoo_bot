import pytest

from bot.handlers.menu import (
    STALE_SESSION_TEXT,
    handle_stale_reply_keyboard,
    show_main_menu,
)
from bot.keyboards import BACK_BUTTON, MAIN_MENU_BUTTON, client_menu_kb, master_menu_kb


class FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class FakeState:
    def __init__(self):
        self.clear_called = False

    async def clear(self):
        self.clear_called = True


class FakeMessage:
    def __init__(self, text: str, user_id: int = 123):
        self.text = text
        self.from_user = FakeUser(user_id)
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


@pytest.mark.anyio
async def test_global_main_menu_clears_state_and_shows_client_menu(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("ADMIN_ID", raising=False)
    state = FakeState()
    message = FakeMessage(MAIN_MENU_BUTTON)

    await show_main_menu(message=message, state=state, session=None)

    assert state.clear_called is True
    assert message.answers == [("Главное меню", client_menu_kb)]


@pytest.mark.anyio
async def test_stale_back_button_returns_admin_to_main_menu(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    state = FakeState()
    message = FakeMessage(BACK_BUTTON, user_id=123)

    await handle_stale_reply_keyboard(message=message, state=state, session=None)

    assert state.clear_called is True
    assert message.answers == [("Главное меню", master_menu_kb)]


@pytest.mark.anyio
async def test_stale_context_button_reports_expired_session(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("ADMIN_ID", raising=False)
    state = FakeState()
    message = FakeMessage("Эскиз 1 — цена договорная")

    await handle_stale_reply_keyboard(message=message, state=state, session=None)

    assert state.clear_called is True
    assert message.answers == [(STALE_SESSION_TEXT, client_menu_kb)]
