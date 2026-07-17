from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Sketch, Style


async def get_all_styles(session: AsyncSession) -> list | None:
    stmt = await session.execute(select(Style))
    styles = stmt.scalars().all()

    if len(styles) == 0:
        return None

    return list(styles)


async def get_style_by_name(session: AsyncSession, style_name: str) -> Style | None:
    result = await session.execute(
        select(Style).where(Style.name == style_name.strip())
    )
    return result.scalar_one_or_none()


async def get_style_by_id(session: AsyncSession, style_id: int) -> Style | None:
    result = await session.execute(select(Style).where(Style.id == style_id))
    return result.scalar_one_or_none()


async def create_style(session: AsyncSession, style_name: str) -> Style:
    existing_style = await get_style_by_name(
        session=session,
        style_name=style_name,
    )

    if existing_style:
        return existing_style

    style = Style(name=style_name)

    session.add(style)
    await session.commit()
    await session.refresh(style)

    return style


async def count_sketches_by_style_id(session: AsyncSession, style_id: int) -> int:
    result = await session.execute(
        select(func.count(Sketch.id)).where(Sketch.style_id == style_id)
    )
    return int(result.scalar_one())


async def update_style_name(
    session: AsyncSession,
    style_id: int,
    style_name: str,
) -> Style | None:
    style = await get_style_by_id(session=session, style_id=style_id)

    if not style:
        return None

    style.name = style_name.strip()
    await session.commit()
    await session.refresh(style)
    return style


async def delete_style(session: AsyncSession, style_id: int) -> bool:
    result = await session.execute(delete(Style).where(Style.id == style_id))
    await session.commit()
    return bool(result.rowcount)
