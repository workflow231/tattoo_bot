from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from db.models import Style


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
