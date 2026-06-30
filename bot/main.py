import os

from aiogram import Bot, Dispatcher
import asyncio

from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers.start import router as start_router

from dotenv import load_dotenv

from utils.logger import logger

from bot.middlewares.db import DbSessionMiddleware

load_dotenv()

async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    redis_url = os.getenv("REDIS_URL")

    storage = RedisStorage.from_url(
        redis_url,
        state_ttl=3600,
        data_ttl=3600,
    )

    bot = Bot(token=token)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(start_router)

    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot crashed")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
