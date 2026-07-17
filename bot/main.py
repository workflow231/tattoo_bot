import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.handlers.admin_calendar import router as admin_calendar_router
from bot.handlers.admin_appointments import router as admin_appointments_router
from bot.handlers.admin_sketches import router as admin_sketches_router
from bot.handlers.admin_working_hours import router as admin_working_hours_router
from bot.handlers.appointments import router as appointments_router
from bot.handlers.client_calendar import router as client_calendar_router
from bot.handlers.menu import router as menu_router
from bot.handlers.start import router as start_router
from bot.handlers.sketch_catalog_handler import router as sketch_catalog_router

from dotenv import load_dotenv

from utils.logger import logger
from utils.config import get_int_env, get_required_env
from services.reminder_scheduler import start_reminder_scheduler

from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.update_idempotency import UpdateIdempotencyMiddleware

load_dotenv()


async def main() -> None:
    token = get_required_env("BOT_TOKEN")
    redis_url = get_required_env("REDIS_URL")
    bot_mode = os.getenv("BOT_MODE", "polling").strip().lower()

    storage = RedisStorage.from_url(
        redis_url,
        state_ttl=3600,
        data_ttl=3600,
    )

    bot = Bot(token=token)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(UpdateIdempotencyMiddleware())
    dp.update.middleware(DbSessionMiddleware())

    _include_routers(dp)

    if bot_mode == "polling":
        await _run_polling(bot=bot, dp=dp, storage=storage)
        return

    if bot_mode == "webhook":
        await _run_webhook(bot=bot, dp=dp, storage=storage)
        return

    await bot.session.close()
    await storage.close()
    raise RuntimeError("BOT_MODE must be polling or webhook")


def _include_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(admin_calendar_router)
    dp.include_router(admin_appointments_router)
    dp.include_router(admin_sketches_router)
    dp.include_router(admin_working_hours_router)
    dp.include_router(client_calendar_router)
    dp.include_router(appointments_router)
    dp.include_router(sketch_catalog_router)
    dp.include_router(menu_router)


async def _run_polling(
    bot: Bot,
    dp: Dispatcher,
    storage: RedisStorage,
) -> None:
    reminder_scheduler = start_reminder_scheduler(bot=bot)

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot crashed")
    finally:
        reminder_scheduler.shutdown(wait=False)
        await storage.close()
        await bot.session.close()


async def _run_webhook(
    bot: Bot,
    dp: Dispatcher,
    storage: RedisStorage,
) -> None:
    webhook_url = get_required_env("WEBHOOK_URL").rstrip("/")
    webhook_path = _get_webhook_path()
    webhook_secret_token = get_required_env("WEBHOOK_SECRET_TOKEN")
    webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    webhook_port = get_int_env("WEBHOOK_PORT", 8080)
    app = web.Application()
    reminder_scheduler = start_reminder_scheduler(bot=bot)

    async def on_shutdown(_: web.Application) -> None:
        reminder_scheduler.shutdown(wait=False)
        await storage.close()
        await bot.session.close()

    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/health", _healthcheck)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_secret_token,
    ).register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=webhook_host, port=webhook_port)

    try:
        await site.start()
        await bot.set_webhook(
            url=f"{webhook_url}{webhook_path}",
            allowed_updates=dp.resolve_used_update_types(),
            secret_token=webhook_secret_token,
        )
        await asyncio.Event().wait()
    except Exception:
        logger.exception("Webhook bot crashed")
    finally:
        await runner.cleanup()


def _get_webhook_path() -> str:
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook").strip()

    if not webhook_path.startswith("/"):
        raise RuntimeError("WEBHOOK_PATH must start with /")

    return webhook_path


async def _healthcheck(_: web.Request) -> web.Response:
    return web.Response(text="ok")


if __name__ == "__main__":
    asyncio.run(main())
