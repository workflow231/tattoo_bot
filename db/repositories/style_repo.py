from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from db.models import Style


async def get_all_styles(session: AsyncSession) -> list | None:
    stmt = await session.execute(select(Style))
    styles = stmt.scalars().all()

    if len(styles) == 0:
        return None

    return list(styles)


async def create_style(session: AsyncSession, style_name: str) -> bool:
    style = Style(name=style_name)

    session.add(style)
    await session.commit()

    return True
