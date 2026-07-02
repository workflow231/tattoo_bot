from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import CHAT_WITH_MASTER_BUTTON, menu_kb
from services.master_contact_service import MasterContactService

router = Router()


@router.message(F.text == CHAT_WITH_MASTER_BUTTON)
async def show_master_contact(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        MasterContactService().get_contact_text(),
        reply_markup=menu_kb,
    )
