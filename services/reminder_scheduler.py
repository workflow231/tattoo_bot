from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db.session import SessionLocal
from services.reminder_service import ReminderService
from utils.logger import logger
from utils.reminder_time import REMINDER_HOUR, REMINDER_MINUTE


def start_reminder_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _send_tomorrow_reminders,
        CronTrigger(hour=REMINDER_HOUR, minute=REMINDER_MINUTE),
        kwargs={"bot": bot},
        id="send_tomorrow_reminders",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler


async def _send_tomorrow_reminders(bot: Bot) -> None:
    try:
        async with SessionLocal() as session:
            await ReminderService(session=session, bot=bot).send_tomorrow_reminders()
    except Exception:
        logger.exception("Failed to send appointment reminders")
