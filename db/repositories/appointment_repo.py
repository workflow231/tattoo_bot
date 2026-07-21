from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Appointment

BUSY_APPOINTMENT_STATUSES = ("pending", "confirmed")


async def create_appointment(
    session: AsyncSession,
    user_id: int,
    sketch_id: int | None,
    appointment_date: date,
    appointment_time: time,
    request_type: str = "catalog_sketch",
    client_sketch_photo_file_id: str | None = None,
    client_comment: str | None = None,
    admin_comment: str | None = None,
    status: str = "pending",
) -> Appointment:
    appointment = Appointment(
        user_id=user_id,
        sketch_id=sketch_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        request_type=request_type,
        client_sketch_photo_file_id=client_sketch_photo_file_id,
        client_comment=client_comment,
        admin_comment=admin_comment,
        status=status,
        reminder_sent=False,
    )

    session.add(appointment)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    await session.refresh(appointment)

    return appointment


async def find_appointment_by_id(
    session: AsyncSession,
    appointment_id: int,
) -> Appointment | None:
    result = await session.execute(
        select(Appointment)
        .options(
            selectinload(Appointment.sketch),
            selectinload(Appointment.user),
        )
        .where(Appointment.id == appointment_id)
    )
    return result.scalar_one_or_none()


async def find_user_appointment_by_id(
    session: AsyncSession,
    user_id: int,
    appointment_id: int,
) -> Appointment | None:
    result = await session.execute(
        select(Appointment)
        .options(selectinload(Appointment.sketch))
        .where(
            Appointment.id == appointment_id,
            Appointment.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_user_appointments(
    session: AsyncSession,
    user_id: int,
) -> list[Appointment]:
    result = await session.execute(
        select(Appointment)
        .options(selectinload(Appointment.sketch))
        .where(Appointment.user_id == user_id)
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc(),
        )
    )
    return list(result.scalars().all())


async def change_appointment_status(
    session: AsyncSession,
    appointment_id: int,
    status: str,
) -> Appointment | None:
    appointment = await find_appointment_by_id(
        session=session,
        appointment_id=appointment_id,
    )

    if not appointment:
        return None

    appointment.status = status

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    await session.refresh(appointment)
    return await find_appointment_by_id(
        session=session,
        appointment_id=appointment_id,
    )


async def exists_confirmed_appointment_for_slot(
    session: AsyncSession,
    appointment: Appointment,
) -> bool:
    result = await session.execute(
        select(Appointment.id).where(
            Appointment.id != appointment.id,
            Appointment.appointment_date == appointment.appointment_date,
            Appointment.appointment_time == appointment.appointment_time,
            Appointment.status == "confirmed",
        )
    )
    return result.scalar_one_or_none() is not None


async def list_confirmed_times_for_date(
    session: AsyncSession,
    appointment_date: date,
) -> list[time]:
    result = await session.execute(
        select(Appointment.appointment_time).where(
            Appointment.appointment_date == appointment_date,
            Appointment.status == "confirmed",
        )
    )
    return list(result.scalars().all())


async def list_busy_times_for_date(
    session: AsyncSession,
    appointment_date: date,
) -> list[time]:
    result = await session.execute(
        select(Appointment.appointment_time).where(
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(BUSY_APPOINTMENT_STATUSES),
        )
    )
    return list(result.scalars().all())


async def count_appointments_by_day(
    session: AsyncSession,
    start_date: date,
    end_date: date,
) -> dict[date, int]:
    result = await session.execute(
        select(
            Appointment.appointment_date,
            func.count(Appointment.id),
        )
        .where(
            Appointment.appointment_date >= start_date,
            Appointment.appointment_date <= end_date,
            Appointment.status.in_(BUSY_APPOINTMENT_STATUSES),
        )
        .group_by(Appointment.appointment_date)
    )
    return {
        appointment_date: appointment_count
        for appointment_date, appointment_count in result.all()
    }


async def list_appointments_for_day(
    session: AsyncSession,
    appointment_date: date,
) -> list[Appointment]:
    result = await session.execute(
        select(Appointment)
        .options(
            selectinload(Appointment.user),
            selectinload(Appointment.sketch),
        )
        .where(
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(BUSY_APPOINTMENT_STATUSES),
        )
        .order_by(Appointment.appointment_time.asc())
    )
    return list(result.scalars().all())


async def list_tomorrow_confirmed_without_reminder(
    session: AsyncSession,
    tomorrow: date,
) -> list[Appointment]:
    result = await session.execute(
        select(Appointment)
        .options(
            selectinload(Appointment.user),
            selectinload(Appointment.sketch),
        )
        .where(
            Appointment.appointment_date == tomorrow,
            Appointment.status == "confirmed",
            Appointment.reminder_sent.is_(False),
        )
        .order_by(Appointment.appointment_time.asc())
    )
    return list(result.scalars().all())


async def mark_reminder_sent(
    session: AsyncSession,
    appointment_id: int,
) -> None:
    appointment = await find_appointment_by_id(
        session=session,
        appointment_id=appointment_id,
    )

    if not appointment:
        return

    appointment.reminder_sent = True
    await session.commit()


async def find_appointment_by_status(
    session: AsyncSession,
    status: str,
) -> list[Appointment]:
    result = await session.execute(
        select(Appointment)
        .options(selectinload(Appointment.user))
        .where(Appointment.status == status)
        .order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc(),
        )
    )
    return list(result.scalars().all())


async def list_appointments(
    session: AsyncSession,
) -> list[Appointment]:
    result = await session.execute(
        select(Appointment)
        .options(selectinload(Appointment.user))
        .order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc(),
        )
    )
    return list(result.scalars().all())
