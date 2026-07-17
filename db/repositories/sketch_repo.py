from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment, Sketch


async def get_available_sketches_by_style_id(
    session: AsyncSession,
    style_id: int,
) -> list[Sketch]:
    stmt = (
        select(Sketch)
        .where(
            Sketch.style_id == style_id,
            Sketch.status == "available",
            Sketch.photo_file_id.is_not(None),
        )
        .order_by(Sketch.views.desc())
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_all_sketches_with_style(session: AsyncSession) -> list[Sketch]:
    stmt = (
        select(Sketch)
        .options(selectinload(Sketch.style))
        .order_by(Sketch.created_at.desc(), Sketch.id.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_sketch_by_id_with_style(
    session: AsyncSession,
    sketch_id: int,
) -> Sketch | None:
    stmt = (
        select(Sketch).options(selectinload(Sketch.style)).where(Sketch.id == sketch_id)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def count_appointments_by_sketch_id(
    session: AsyncSession,
    sketch_id: int,
) -> int:
    result = await session.execute(
        select(func.count(Appointment.id)).where(Appointment.sketch_id == sketch_id)
    )
    return int(result.scalar_one())


async def increment_sketch_views(
    session: AsyncSession,
    sketch_id: int,
) -> None:
    await session.execute(
        update(Sketch).where(Sketch.id == sketch_id).values(views=Sketch.views + 1)
    )
    await session.commit()


async def find_viewed_sketch_photo_in_style(
    session: AsyncSession,
    style_id: int,
) -> str | None:
    stmt = (
        select(Sketch.photo_file_id)
        .where(
            Sketch.style_id == style_id,
            Sketch.status == "available",
            Sketch.photo_file_id.is_not(None),
        )
        .order_by(Sketch.views.desc())
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_sketch(
    session: AsyncSession,
    style_id: int,
    name: str,
    description: str | None = None,
    price: int | None = None,
    photo_file_id: str | None = None,
    status: str = "available",
    views: int = 0,
) -> Sketch:
    sketch = Sketch(
        style_id=style_id,
        name=name,
        description=description,
        price=price,
        photo_file_id=photo_file_id,
        status=status,
        views=views,
    )

    session.add(sketch)
    await session.commit()
    await session.refresh(sketch)

    return sketch


async def update_sketch(
    session: AsyncSession,
    sketch_id: int,
    **fields,
) -> Sketch | None:
    sketch = await get_sketch_by_id_with_style(session=session, sketch_id=sketch_id)

    if not sketch:
        return None

    for field_name, field_value in fields.items():
        setattr(sketch, field_name, field_value)

    await session.commit()
    return await get_sketch_by_id_with_style(session=session, sketch_id=sketch.id)


async def delete_sketch(session: AsyncSession, sketch_id: int) -> bool:
    result = await session.execute(delete(Sketch).where(Sketch.id == sketch_id))
    await session.commit()
    return bool(result.rowcount)
