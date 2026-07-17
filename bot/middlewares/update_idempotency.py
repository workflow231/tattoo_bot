from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from db.repositories.processed_update_repo import (
    claim_processed_update,
    release_processed_update,
)
from db.session import SessionLocal


class UpdateIdempotencyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        async with SessionLocal() as session:
            claimed = await claim_processed_update(
                session=session,
                update_id=event.update_id,
            )

        if not claimed:
            return None

        try:
            return await handler(event, data)
        except Exception:
            async with SessionLocal() as session:
                await release_processed_update(
                    session=session,
                    update_id=event.update_id,
                )
            raise
