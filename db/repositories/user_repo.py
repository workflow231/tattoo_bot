from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    is_admin: bool = False,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        is_admin=is_admin,
        created_at=datetime.now(),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> tuple[User, bool]:
    user = await get_user_by_telegram_id(session, telegram_id)

    if user:
        return user, False

    user = await create_user(
        session=session,
        telegram_id=telegram_id,
        username=username,
    )

    return user, True

async def check_user_is_admin(
        session: AsyncSession,
        telegram_id: int,
) -> bool | None:
    stmt = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = stmt.scalar_one_or_none()

    if not user:
        return None

    return user.is_admin

async def change_admin_status(
        session: AsyncSession,
        admin_id: int
) -> bool | None:
    stmt = await session.execute(
        select(User).where(User.telegram_id == admin_id)
    )
    user = stmt.scalar_one_or_none()

    if not user:
        return None

    user.is_admin = True

    await session.commit()

    return True