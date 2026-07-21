from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CHAT_WITH_MASTER_BUTTON,
    MAIN_MENU_BUTTON,
    MY_SOCIALS_BUTTON,
)
from bot.menu_utils import get_main_menu_for_message
from services.client_text_service import ClientTextService
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


@router.message(F.text == MY_SOCIALS_BUTTON)
async def show_my_socials(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()
    await message.answer(
        ClientTextService().my_socials(),
        reply_markup=get_main_menu_for_message(session=session, message=message),
    )


@router.message(F.text == MAIN_MENU_BUTTON)
async def show_main_menu(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()
    await message.answer(
        ClientTextService().text("main_menu"),
        reply_markup=get_main_menu_for_message(session=session, message=message),
    )


@router.message()
async def handle_stale_reply_keyboard(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()
    text = (
        ClientTextService().text("main_menu")
        if message.text == BACK_BUTTON
        else ClientTextService().stale_session()
    )
    await message.answer(
        text,
        reply_markup=get_main_menu_for_message(session=session, message=message),
    )
