from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProcessedUpdate


async def claim_processed_update(session: AsyncSession, update_id: int) -> bool:
    session.add(ProcessedUpdate(update_id=update_id))

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return False

    return True


async def release_processed_update(session: AsyncSession, update_id: int) -> None:
    processed_update = await session.get(ProcessedUpdate, update_id)

    if not processed_update:
        return

    await session.delete(processed_update)
    await session.commit()
