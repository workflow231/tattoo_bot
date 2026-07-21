from types import SimpleNamespace

import pytest

import bot.handlers.start as start_handler
from bot.handlers.start import cmd_start
from bot.keyboards import client_menu_kb, master_menu_kb


class FakeState:
    def __init__(self):
        self.clear_called = False

    async def clear(self):
        self.clear_called = True


class FakeMessage:
    def __init__(self, user_id: int, username: str | None):
        self.from_user = SimpleNamespace(id=user_id, username=username)
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


class FakeSessionLocal:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.anyio
async def test_start_uses_admin_ids_for_menu_even_if_db_flag_is_false(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    monkeypatch.setattr(start_handler, "SessionLocal", FakeSessionLocal)
    monkeypatch.setattr(
        start_handler,
        "UserService",
        _fake_user_service(is_admin=False, created=False),
    )
    state = FakeState()
    message = FakeMessage(user_id=123, username="admin")

    await cmd_start(message=message, state=state)

    assert state.clear_called is True
    assert len(message.answers) == 1
    assert message.answers[0][1] == master_menu_kb


@pytest.mark.anyio
async def test_start_uses_client_menu_when_admin_removed_from_env(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("ADMIN_ID", raising=False)
    monkeypatch.setattr(start_handler, "SessionLocal", FakeSessionLocal)
    monkeypatch.setattr(
        start_handler,
        "UserService",
        _fake_user_service(is_admin=True, created=False),
    )
    state = FakeState()
    message = FakeMessage(user_id=123, username="client")

    await cmd_start(message=message, state=state)

    assert state.clear_called is True
    assert len(message.answers) == 1
    assert message.answers[0][1] == client_menu_kb


def _fake_user_service(is_admin: bool, created: bool):
    class FakeUserService:
        def __init__(self, session):
            self.session = session

        async def register_or_get_user(self, telegram_id: int, username: str | None):
            return SimpleNamespace(is_admin=is_admin), created

    return FakeUserService
