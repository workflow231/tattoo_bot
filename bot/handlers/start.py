from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.services.user_service import UserService

from bot.keyboards import menu_kb
from db.session import SessionLocal

from utils.logger import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with SessionLocal() as session:
        user_service = UserService(session)

        user, created = await user_service.register_or_get_user(
            telegram_id=telegram_id,
            username=username,
        )

    if created:
        logger.info("New user registered: telegram_id=%s", telegram_id)
        await message.answer(text="Добро пожаловать!", reply_markup=menu_kb)
    else:
        logger.info("User already registered: telegram_id=%s", telegram_id)
        await message.answer(text="С возвращением!", reply_markup=menu_kb)
