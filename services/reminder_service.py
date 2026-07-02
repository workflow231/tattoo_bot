from datetime import date, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Appointment
from db.repositories.appointment_repo import (
    list_tomorrow_confirmed_without_reminder,
    mark_reminder_sent,
)
from services.appointment_service import DATE_FORMAT, TIME_FORMAT


class ReminderService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot

    async def send_tomorrow_reminders(self, today: date | None = None) -> int:
        tomorrow = (today or date.today()) + timedelta(days=1)
        appointments = await list_tomorrow_confirmed_without_reminder(
            session=self.session,
            tomorrow=tomorrow,
        )
        sent_count = 0

        for appointment in appointments:
            if not appointment.user:
                continue

            sent = await self.send_reminder(appointment=appointment)

            if not sent:
                continue

            await mark_reminder_sent(
                session=self.session,
                appointment_id=appointment.id,
            )
            sent_count += 1

        return sent_count

    async def send_reminder(self, appointment: Appointment) -> bool:
        if not appointment.user:
            return False

        try:
            await self.bot.send_message(
                chat_id=appointment.user.telegram_id,
                text=self.build_reminder_text(appointment=appointment),
            )
        except TelegramAPIError:
            return False

        return True

    def build_reminder_text(self, appointment: Appointment) -> str:
        sketch_name = appointment.sketch.name if appointment.sketch else "Не указан"

        return (
            "Напоминание о записи\n\n"
            "Завтра у вас сеанс тату.\n\n"
            f"Дата: {appointment.appointment_date.strftime(DATE_FORMAT)}\n"
            f"Время: {appointment.appointment_time.strftime(TIME_FORMAT)}\n"
            f"Эскиз: {sketch_name}\n\n"
            "Если планы изменились — напишите мастеру заранее."
        )
