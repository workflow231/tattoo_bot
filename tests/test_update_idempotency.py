import pytest
from aiogram.types import Update

from bot.middlewares.update_idempotency import UpdateIdempotencyMiddleware


class FakeSession:
    pass


class FakeSessionLocal:
    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.anyio
async def test_update_idempotency_skips_duplicate_update(monkeypatch) -> None:
    handler_called = False

    async def fake_claim_processed_update(session, update_id):
        return False

    async def handler(event, data):
        nonlocal handler_called
        handler_called = True

    monkeypatch.setattr(
        "bot.middlewares.update_idempotency.SessionLocal",
        FakeSessionLocal,
    )
    monkeypatch.setattr(
        "bot.middlewares.update_idempotency.claim_processed_update",
        fake_claim_processed_update,
    )

    result = await UpdateIdempotencyMiddleware()(
        handler,
        Update(update_id=123),
        {},
    )

    assert result is None
    assert handler_called is False


@pytest.mark.anyio
async def test_update_idempotency_releases_claim_on_error(monkeypatch) -> None:
    released_update_ids = []

    async def fake_claim_processed_update(session, update_id):
        return True

    async def fake_release_processed_update(session, update_id):
        released_update_ids.append(update_id)

    async def handler(event, data):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "bot.middlewares.update_idempotency.SessionLocal",
        FakeSessionLocal,
    )
    monkeypatch.setattr(
        "bot.middlewares.update_idempotency.claim_processed_update",
        fake_claim_processed_update,
    )
    monkeypatch.setattr(
        "bot.middlewares.update_idempotency.release_processed_update",
        fake_release_processed_update,
    )

    with pytest.raises(RuntimeError, match="boom"):
        await UpdateIdempotencyMiddleware()(
            handler,
            Update(update_id=456),
            {},
        )

    assert released_update_ids == [456]
