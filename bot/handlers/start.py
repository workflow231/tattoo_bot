from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.user_service import UserService
from services.client_text_service import ClientTextService

from bot.keyboards import get_main_menu
from db.session import SessionLocal

from utils.logger import logger
from utils.config import get_admin_ids_from_env

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    telegram_id = message.from_user.id
    username = message.from_user.username

    async with SessionLocal() as session:
        user_service = UserService(session)

        _, created = await user_service.register_or_get_user(
            telegram_id=telegram_id,
            username=username,
        )

    is_admin = telegram_id in get_admin_ids_from_env()
    reply_markup = get_main_menu(is_admin=is_admin)
    client_texts = ClientTextService()

    if created:
        logger.info("New user registered")
        await message.answer(
            text=client_texts.welcome_new_user(),
            reply_markup=reply_markup,
        )
    else:
        logger.info("User already registered")
        await message.answer(
            text=client_texts.welcome_existing_user(),
            reply_markup=reply_markup,
        )
