import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers.admin_calendar import router as admin_calendar_router
from bot.handlers.admin_appointments import router as admin_appointments_router
from bot.handlers.appointments import router as appointments_router
from bot.handlers.menu import router as menu_router
from bot.handlers.start import router as start_router
from bot.handlers.sketch_catalog_handler import router as sketch_catalog_router

from dotenv import load_dotenv

from utils.logger import logger
from utils.config import get_required_env
from services.reminder_scheduler import start_reminder_scheduler

from bot.middlewares.db import DbSessionMiddleware

load_dotenv()


async def main() -> None:
    token = get_required_env("BOT_TOKEN")
    redis_url = get_required_env("REDIS_URL")

    storage = RedisStorage.from_url(
        redis_url,
        state_ttl=3600,
        data_ttl=3600,
    )

    bot = Bot(token=token)
    dp = Dispatcher(storage=storage)
    reminder_scheduler = start_reminder_scheduler(bot=bot)

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(start_router)
    dp.include_router(admin_calendar_router)
    dp.include_router(admin_appointments_router)
    dp.include_router(appointments_router)
    dp.include_router(sketch_catalog_router)
    dp.include_router(menu_router)

    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot crashed")
    finally:
        reminder_scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
