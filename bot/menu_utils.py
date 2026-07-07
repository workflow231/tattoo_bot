from aiogram.types import Message, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import client_menu_kb, get_main_menu
from services.admin_appointment_service import AdminAppointmentService


def get_main_menu_for_message(
    session: AsyncSession,
    message: Message,
) -> ReplyKeyboardMarkup:
    if not message.from_user:
        return client_menu_kb

    is_admin = AdminAppointmentService(session=session).is_admin(
        telegram_id=message.from_user.id,
    )
    return get_main_menu(is_admin=is_admin)
