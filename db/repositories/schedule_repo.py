from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ScheduleException, WeeklyDayOff

TEMPORARY_DAY_OFF_TYPE = "temporary_day_off"
BLOCKED_SLOT_TYPE = "blocked_slot"


async def find_temporary_day_off(
    session: AsyncSession,
    day: date,
) -> ScheduleException | None:
    result = await session.execute(
        select(ScheduleException).where(
            ScheduleException.date == day,
            ScheduleException.time_slot.is_(None),
            ScheduleException.type == TEMPORARY_DAY_OFF_TYPE,
        )
    )
    return result.scalar_one_or_none()


async def list_temporary_day_offs(
    session: AsyncSession,
    start_date: date,
    end_date: date,
) -> list[ScheduleException]:
    result = await session.execute(
        select(ScheduleException).where(
            ScheduleException.date >= start_date,
            ScheduleException.date <= end_date,
            ScheduleException.time_slot.is_(None),
            ScheduleException.type == TEMPORARY_DAY_OFF_TYPE,
        )
    )
    return list(result.scalars().all())


async def add_temporary_day_off(
    session: AsyncSession,
    day: date,
) -> ScheduleException:
    existing_day_off = await find_temporary_day_off(session=session, day=day)

    if existing_day_off:
        return existing_day_off

    day_off = ScheduleException(
        date=day,
        time_slot=None,
        type=TEMPORARY_DAY_OFF_TYPE,
    )

    session.add(day_off)
    await session.commit()
    await session.refresh(day_off)

    return day_off


async def remove_temporary_day_off(
    session: AsyncSession,
    day: date,
) -> bool:
    existing_day_off = await find_temporary_day_off(session=session, day=day)

    if not existing_day_off:
        return False

    await session.delete(existing_day_off)
    await session.commit()
    return True


async def find_weekly_day_off(
    session: AsyncSession,
    weekday: int,
) -> WeeklyDayOff | None:
    result = await session.execute(
        select(WeeklyDayOff).where(WeeklyDayOff.weekday == weekday)
    )
    return result.scalar_one_or_none()


async def list_weekly_day_offs(
    session: AsyncSession,
) -> list[WeeklyDayOff]:
    result = await session.execute(select(WeeklyDayOff))
    return list(result.scalars().all())


async def add_weekly_day_off(
    session: AsyncSession,
    weekday: int,
) -> WeeklyDayOff:
    existing_day_off = await find_weekly_day_off(
        session=session,
        weekday=weekday,
    )

    if existing_day_off:
        return existing_day_off

    day_off = WeeklyDayOff(weekday=weekday)

    session.add(day_off)
    await session.commit()
    await session.refresh(day_off)

    return day_off


async def remove_weekly_day_off(
    session: AsyncSession,
    weekday: int,
) -> bool:
    existing_day_off = await find_weekly_day_off(
        session=session,
        weekday=weekday,
    )

    if not existing_day_off:
        return False

    await session.delete(existing_day_off)
    await session.commit()
    return True


async def find_blocked_slot(
    session: AsyncSession,
    day: date,
    time_slot: time,
) -> ScheduleException | None:
    result = await session.execute(
        select(ScheduleException).where(
            ScheduleException.date == day,
            ScheduleException.time_slot == time_slot,
            ScheduleException.type == BLOCKED_SLOT_TYPE,
        )
    )
    return result.scalar_one_or_none()


async def list_blocked_slots_for_day(
    session: AsyncSession,
    day: date,
) -> list[ScheduleException]:
    result = await session.execute(
        select(ScheduleException)
        .where(
            ScheduleException.date == day,
            ScheduleException.time_slot.is_not(None),
            ScheduleException.type == BLOCKED_SLOT_TYPE,
        )
        .order_by(ScheduleException.time_slot.asc())
    )
    return list(result.scalars().all())


async def list_blocked_slots(
    session: AsyncSession,
    start_date: date,
    end_date: date,
) -> list[ScheduleException]:
    result = await session.execute(
        select(ScheduleException).where(
            ScheduleException.date >= start_date,
            ScheduleException.date <= end_date,
            ScheduleException.time_slot.is_not(None),
            ScheduleException.type == BLOCKED_SLOT_TYPE,
        )
    )
    return list(result.scalars().all())


async def add_blocked_slot(
    session: AsyncSession,
    day: date,
    time_slot: time,
) -> ScheduleException:
    existing_slot = await find_blocked_slot(
        session=session,
        day=day,
        time_slot=time_slot,
    )

    if existing_slot:
        return existing_slot

    blocked_slot = ScheduleException(
        date=day,
        time_slot=time_slot,
        type=BLOCKED_SLOT_TYPE,
    )

    session.add(blocked_slot)
    await session.commit()
    await session.refresh(blocked_slot)

    return blocked_slot


async def remove_blocked_slot(
    session: AsyncSession,
    day: date,
    time_slot: time,
) -> bool:
    existing_slot = await find_blocked_slot(
        session=session,
        day=day,
        time_slot=time_slot,
    )

    if not existing_slot:
        return False

    await session.delete(existing_slot)
    await session.commit()
    return True
