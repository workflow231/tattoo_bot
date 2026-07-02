from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    ADMIN_ALL_APPOINTMENTS_BUTTON,
    ADMIN_APPOINTMENTS_BUTTON,
    ADMIN_APPROVE_APPOINTMENT_BUTTON,
    ADMIN_BACK_TO_APPOINTMENTS_BUTTON,
    ADMIN_CONFIRMED_APPOINTMENTS_BUTTON,
    ADMIN_PENDING_APPOINTMENTS_BUTTON,
    ADMIN_REJECT_APPOINTMENT_BUTTON,
    ADMIN_REJECTED_APPOINTMENTS_BUTTON,
    ADMIN_WRITE_CLIENT_BUTTON,
    BACK_BUTTON,
    MAIN_MENU_BUTTON,
    build_admin_appointment_card_keyboard,
    build_admin_appointment_filters_keyboard,
    build_admin_appointments_keyboard,
    menu_kb,
)
from bot.states import AdminAppointmentState
from services.admin_appointment_service import AdminAppointmentService

router = Router()

ADMIN_FILTER_BUTTONS = {
    ADMIN_PENDING_APPOINTMENTS_BUTTON,
    ADMIN_CONFIRMED_APPOINTMENTS_BUTTON,
    ADMIN_REJECTED_APPOINTMENTS_BUTTON,
    ADMIN_ALL_APPOINTMENTS_BUTTON,
}


@router.message(F.text == ADMIN_APPOINTMENTS_BUTTON)
async def show_admin_appointment_filters(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    await state.set_state(AdminAppointmentState.choosing_filter)
    await message.answer(
        "Выберите список заявок:",
        reply_markup=build_admin_appointment_filters_keyboard(),
    )


@router.message(AdminAppointmentState.choosing_filter)
async def choose_admin_appointment_filter(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    if message.text not in ADMIN_FILTER_BUTTONS:
        await message.answer(
            "Выберите фильтр кнопкой.",
            reply_markup=build_admin_appointment_filters_keyboard(),
        )
        return

    await _send_admin_appointments_list(
        session=session,
        message=message,
        state=state,
        filter_text=message.text,
    )


@router.message(AdminAppointmentState.choosing_appointment)
async def choose_admin_appointment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AdminAppointmentState.choosing_filter)
        await message.answer(
            "Выберите список заявок:",
            reply_markup=build_admin_appointment_filters_keyboard(),
        )
        return

    data = await state.get_data()
    appointment_buttons: dict[str, int] = data.get("admin_appointment_buttons", {})
    appointment_id = appointment_buttons.get(message.text or "")

    if not appointment_id:
        await message.answer("Выберите заявку кнопкой из списка.")
        return

    service = AdminAppointmentService(session=session)
    card_text = await service.get_appointment_card(appointment_id=appointment_id)

    if not card_text:
        await message.answer("Заявка не найдена.")
        return

    await state.update_data(selected_admin_appointment_id=appointment_id)
    await state.set_state(AdminAppointmentState.viewing_appointment)
    await message.answer(
        card_text,
        reply_markup=build_admin_appointment_card_keyboard(),
    )


@router.message(AdminAppointmentState.viewing_appointment)
async def view_admin_appointment_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    if message.text == ADMIN_BACK_TO_APPOINTMENTS_BUTTON:
        data = await state.get_data()
        filter_text = data.get("admin_appointment_filter")

        if not filter_text:
            await state.set_state(AdminAppointmentState.choosing_filter)
            await message.answer(
                "Выберите список заявок:",
                reply_markup=build_admin_appointment_filters_keyboard(),
            )
            return

        await _send_admin_appointments_list(
            session=session,
            message=message,
            state=state,
            filter_text=filter_text,
        )
        return

    if message.text == ADMIN_WRITE_CLIENT_BUTTON:
        await _send_client_contact(
            session=session,
            message=message,
            state=state,
        )
        return

    if message.text == ADMIN_APPROVE_APPOINTMENT_BUTTON:
        await _handle_admin_appointment_action(
            session=session,
            message=message,
            state=state,
            action="confirm",
        )
        return

    if message.text == ADMIN_REJECT_APPOINTMENT_BUTTON:
        await _handle_admin_appointment_action(
            session=session,
            message=message,
            state=state,
            action="reject",
        )
        return

    await message.answer(
        "Выберите действие кнопкой.",
        reply_markup=build_admin_appointment_card_keyboard(),
    )


async def _send_client_contact(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    appointment_id = data.get("selected_admin_appointment_id")

    if not appointment_id:
        await message.answer("Заявка не выбрана.")
        return

    service = AdminAppointmentService(session=session)
    contact_text = await service.get_client_contact_text(appointment_id=appointment_id)

    if not contact_text:
        await message.answer("Заявка не найдена.")
        return

    await message.answer(
        contact_text,
        reply_markup=build_admin_appointment_card_keyboard(),
    )


async def _handle_admin_appointment_action(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    action: str,
) -> None:
    data = await state.get_data()
    appointment_id = data.get("selected_admin_appointment_id")

    if not appointment_id:
        await message.answer("Заявка не выбрана.")
        return

    service = AdminAppointmentService(session=session)

    if action == "confirm":
        result = await service.confirm_appointment(appointment_id=appointment_id)
    else:
        result = await service.reject_appointment(appointment_id=appointment_id)

    notification_sent = await _send_client_notification(
        message=message,
        chat_id=result.client_chat_id,
        text=result.client_message,
    )
    admin_message = result.admin_message

    if result.client_message and not notification_sent:
        admin_message += "\n\nНе удалось отправить уведомление клиенту."

    card_text = await service.get_appointment_card(appointment_id=appointment_id)

    if card_text:
        await message.answer(
            admin_message + "\n\n" + card_text,
            reply_markup=build_admin_appointment_card_keyboard(),
        )
        return

    await state.clear()
    await message.answer(admin_message, reply_markup=menu_kb)


async def _send_client_notification(
    message: Message,
    chat_id: int | None,
    text: str | None,
) -> bool:
    if not chat_id or not text:
        return False

    try:
        await message.bot.send_message(chat_id=chat_id, text=text)
    except TelegramAPIError:
        return False

    return True


async def _send_admin_appointments_list(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    filter_text: str,
) -> None:
    service = AdminAppointmentService(session=session)
    appointments = await service.list_appointments_by_filter(filter_text=filter_text)

    await state.update_data(admin_appointment_filter=filter_text)

    if not appointments:
        await state.set_state(AdminAppointmentState.choosing_filter)
        await message.answer(
            "Заявок по этому фильтру нет.",
            reply_markup=build_admin_appointment_filters_keyboard(),
        )
        return

    appointment_buttons = {
        f"Открыть #{appointment.id}": appointment.id for appointment in appointments
    }

    await state.update_data(admin_appointment_buttons=appointment_buttons)
    await state.set_state(AdminAppointmentState.choosing_appointment)
    await message.answer(
        service.build_admin_list_title(filter_text)
        + "\n\n"
        + "\n".join(appointment.text for appointment in appointments),
        reply_markup=build_admin_appointments_keyboard(appointments),
    )


async def _handle_common_navigation(
    message: Message,
    state: FSMContext,
) -> bool:
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return True

    return False


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)
