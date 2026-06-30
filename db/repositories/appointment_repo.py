from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment


async def create_appointment(
        session: AsyncSession,
        user_id: int,
        sketch_id: int,
        appointment_date: date,
        appointment_time: time,
        client_comment: str | None = None,
        admin_comment: str | None = None,
        reminder_time: bool = True
) -> Appointment:

    appointment = Appointment(
        session=session,
        user_id=user_id,
        sketch_id=sketch_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        client_comment=client_comment,
        admin_comment=admin_comment,
        reminder_time=reminder_time
    )

    session.add(appointment)
    await session.commit()
    await session.refresh(appointment)

    return appointment

async def find_appointment_by_id(
        session: AsyncSession,
        appointment_id: id
) -> Appointment | None:
    stmt = await session.execute(select(Appointment).where(Appointment.id==appointment_id))
    appointment = stmt.scalar_one_or_none()

    if not appointment:
        return None

    return appointment

async def change_appointment_status(
        session: AsyncSession,
        appointment_id: int,
        status: str
) -> bool:
    appointment = await find_appointment_by_id(
        session=session,
        appointment_id=appointment_id
    )

    if not appointment:
        return False

    appointment.status = status

    await session.commit()
    return True

async def find_appointment_by_status(
        session: AsyncSession,
        status: str
) -> list[Appointment] | None:
    stmt = await session.execute(select(Appointment).where(Appointment.status == status))
    appointments = stmt.scalars().all()

    if len(appointments) == 0:
        return None

    return list(appointments)