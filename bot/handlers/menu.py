from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import CHAT_WITH_MASTER_BUTTON
from bot.menu_utils import get_main_menu_for_message
from services.master_contact_service import MasterContactService

router = Router()


@router.message(F.text == CHAT_WITH_MASTER_BUTTON)
async def show_master_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    await message.answer(
        MasterContactService().get_contact_text(),
        reply_markup=get_main_menu_for_message(session=session, message=message),
    )
