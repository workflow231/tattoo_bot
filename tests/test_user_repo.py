import pytest
from sqlalchemy.exc import IntegrityError

from db.repositories.user_repo import get_or_create_user


class FakeSession:
    def __init__(self):
        self.rollback_called = False

    async def rollback(self):
        self.rollback_called = True


@pytest.mark.anyio
async def test_get_or_create_user_handles_parallel_create_race(monkeypatch) -> None:
    session = FakeSession()
    user = type("UserStub", (), {"id": 1, "telegram_id": 123})()
    get_calls = 0

    async def fake_get_user_by_telegram_id(session, telegram_id):
        nonlocal get_calls
        get_calls += 1
        return None if get_calls == 1 else user

    async def fake_create_user(session, telegram_id, username):
        raise IntegrityError("statement", {}, Exception("unique"))

    monkeypatch.setattr(
        "db.repositories.user_repo.get_user_by_telegram_id",
        fake_get_user_by_telegram_id,
    )
    monkeypatch.setattr("db.repositories.user_repo.create_user", fake_create_user)

    result_user, created = await get_or_create_user(
        session=session,
        telegram_id=123,
        username="user",
    )

    assert result_user is user
    assert created is False
    assert session.rollback_called is True
