from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    ADMIN_APPROVE_APPOINTMENT_BUTTON,
    ADMIN_BACK_TO_CALENDAR_DAY_BUTTON,
    ADMIN_CALENDAR_CALLBACK_PREFIX,
    ADMIN_CALENDAR_IGNORE_CALLBACK,
    ADMIN_REJECT_APPOINTMENT_BUTTON,
    ADMIN_WRITE_CLIENT_BUTTON,
    CALENDAR_BUTTON,
    MAIN_MENU_BUTTON,
    build_admin_calendar_appointment_card_inline_keyboard,
    build_admin_calendar_day_inline_keyboard,
    build_admin_calendar_keyboard,
    build_admin_calendar_inline_keyboard,
    build_admin_day_off_type_inline_keyboard,
    build_admin_slot_inline_keyboard,
    master_menu_kb,
)
from bot.states import AdminCalendarState
from services.admin_appointment_service import AdminAppointmentService
from services.admin_calendar_service import AdminCalendarService

router = Router()


@router.callback_query(F.data == ADMIN_CALENDAR_IGNORE_CALLBACK)
async def ignore_calendar_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(F.text == CALENDAR_BUTTON)
async def show_admin_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.")
        return

    await message.answer(
        "Календарь мастера открыт.",
        reply_markup=build_admin_calendar_keyboard([]),
    )
    today = date.today()
    await _send_admin_calendar_month(
        session=session,
        message=message,
        state=state,
        year=today.year,
        month=today.month,
    )


@router.callback_query(F.data.startswith(f"{ADMIN_CALENDAR_CALLBACK_PREFIX}:"))
async def handle_admin_calendar_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    if not callback.message:
        await callback.answer()
        return

    if not _callback_from_admin(session=session, callback=callback):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    data = callback.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if await _handle_admin_calendar_navigation_callback(
        session=session,
        callback=callback,
        state=state,
        action=action,
        parts=parts,
    ):
        return

    if await _handle_admin_calendar_day_action_callback(
        session=session,
        callback=callback,
        state=state,
        action=action,
        parts=parts,
    ):
        return

    if await _handle_admin_calendar_appointment_callback(
        session=session,
        callback=callback,
        state=state,
        action=action,
        parts=parts,
    ):
        return

    await callback.answer()


async def _handle_admin_calendar_navigation_callback(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    action: str,
    parts: list[str],
) -> bool:
    if action == "month" and len(parts) == 4:
        await _edit_admin_calendar_month(
            session=session,
            callback=callback,
            state=state,
            year=int(parts[2]),
            month=int(parts[3]),
        )
        return True

    if action == "day" and len(parts) == 3:
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=date.fromisoformat(parts[2]),
        )
        return True

    appointment_date = await _get_state_admin_calendar_date(state=state)

    if action == "back_month" and appointment_date:
        await _edit_admin_calendar_month(
            session=session,
            callback=callback,
            state=state,
            year=appointment_date.year,
            month=appointment_date.month,
        )
        return True

    if action == "back_day" and appointment_date:
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    return False


async def _handle_admin_calendar_day_action_callback(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    action: str,
    parts: list[str],
) -> bool:
    appointment_date = await _get_state_admin_calendar_date(state=state)

    if (
        action
        in {
            "add_day_off",
            "day_off",
            "block_slot",
            "block_slot_time",
            "remove_temp",
            "remove_weekly",
            "remove_block",
        }
        and not appointment_date
    ):
        await callback.answer("Дата не выбрана.", show_alert=True)
        return True

    if action == "add_day_off":
        await state.set_state(AdminCalendarState.choosing_day_off_type)
        await callback.message.edit_text(
            "Какой выходной добавить?",
            reply_markup=build_admin_day_off_type_inline_keyboard(),
        )
        await callback.answer()
        return True

    if action == "day_off" and len(parts) == 3:
        service = AdminCalendarService(session=session)
        if parts[2] == "weekly":
            result_text = await service.add_weekly_day_off(
                appointment_date=appointment_date,
            )
        else:
            result_text = await service.add_temporary_day_off(
                appointment_date=appointment_date,
            )

        await callback.answer(result_text)
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    if action == "block_slot":
        service = AdminCalendarService(session=session)
        slot_texts = await service.get_blockable_slot_texts(
            appointment_date=appointment_date,
        )
        await state.set_state(AdminCalendarState.choosing_slot)
        await callback.message.edit_text(
            (
                "Выберите слот для блокировки:"
                if slot_texts
                else "На эту дату рабочие слоты не заданы."
            ),
            reply_markup=build_admin_slot_inline_keyboard(slot_texts),
        )
        await callback.answer()
        return True

    if action == "block_slot_time" and len(parts) == 3:
        time_text = parts[2].replace("-", ":")
        service = AdminCalendarService(session=session)
        result_text = await service.add_blocked_slot(
            appointment_date=appointment_date,
            time_text=time_text,
        )

        if not result_text:
            await callback.answer("Некорректный слот.", show_alert=True)
            return True

        await callback.answer(result_text)
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    if action == "remove_temp":
        service = AdminCalendarService(session=session)
        await callback.answer(
            await service.remove_temporary_day_off(appointment_date=appointment_date)
        )
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    if action == "remove_weekly":
        service = AdminCalendarService(session=session)
        await callback.answer(
            await service.remove_weekly_day_off(appointment_date=appointment_date)
        )
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    if action == "remove_block" and len(parts) == 3:
        time_text = parts[2].replace("-", ":")
        service = AdminCalendarService(session=session)
        result_text = await service.remove_blocked_slot(
            appointment_date=appointment_date,
            time_text=time_text,
        )
        await callback.answer(result_text or "Блокировка не найдена.")
        await _edit_admin_calendar_day(
            session=session,
            callback=callback,
            state=state,
            appointment_date=appointment_date,
        )
        return True

    return False


async def _handle_admin_calendar_appointment_callback(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    action: str,
    parts: list[str],
) -> bool:
    if action == "appointment" and len(parts) == 3:
        await _edit_admin_calendar_appointment_card(
            session=session,
            callback=callback,
            state=state,
            appointment_id=int(parts[2]),
        )
        return True

    if action in {"confirm", "reject"} and len(parts) == 3:
        await _handle_admin_calendar_appointment_action_callback(
            session=session,
            callback=callback,
            state=state,
            appointment_id=int(parts[2]),
            action=action,
        )
        return True

    if action == "client" and len(parts) == 3:
        service = AdminAppointmentService(session=session)
        contact_text = await service.get_client_contact_text(
            appointment_id=int(parts[2])
        )
        await callback.message.answer(contact_text or "Заявка не найдена.")
        await callback.answer()
        return True

    return False


@router.message(AdminCalendarState.viewing_month)
async def navigate_admin_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    await message.answer("Используйте inline-кнопки календаря.")


@router.message(AdminCalendarState.viewing_day)
async def view_admin_calendar_day(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if message.text == "⬅️ Назад":
        data = await state.get_data()
        appointment_date = _parse_state_date(data.get("admin_calendar_date"))

        if appointment_date:
            await _send_admin_calendar_month(
                session=session,
                message=message,
                state=state,
                year=appointment_date.year,
                month=appointment_date.month,
            )
            return

        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.set_state(AdminCalendarState.viewing_month)
        await message.answer("Дата не выбрана.", reply_markup=master_menu_kb)
        return

    await message.answer("Используйте inline-кнопки дня.")


@router.message(AdminCalendarState.choosing_slot)
async def choose_admin_blocked_slot(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.clear()
        await message.answer("Дата не выбрана.", reply_markup=master_menu_kb)
        return

    if message.text == "⬅️ Назад":
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    await message.answer("Выберите слот inline-кнопкой.")


@router.message(AdminCalendarState.choosing_day_off_type)
async def choose_admin_day_off_type(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.clear()
        await message.answer("Дата не выбрана.", reply_markup=master_menu_kb)
        return

    if message.text == "⬅️ Назад":
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    await message.answer("Выберите тип выходного inline-кнопкой.")


@router.message(AdminCalendarState.viewing_appointment)
async def view_admin_calendar_appointment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if message.text == ADMIN_BACK_TO_CALENDAR_DAY_BUTTON:
        data = await state.get_data()
        appointment_date = _parse_state_date(data.get("admin_calendar_date"))

        if not appointment_date:
            await state.clear()
            await message.answer("Дата не выбрана.", reply_markup=master_menu_kb)
            return

        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
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

    data = await state.get_data()
    appointment_id = data.get("selected_admin_calendar_appointment_id")

    if not appointment_id:
        await message.answer("Заявка не выбрана.")
        return

    await message.answer(
        "Выберите действие кнопкой.",
        reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
            appointment_id=int(appointment_id),
        ),
    )


async def _send_admin_calendar_month(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    year: int,
    month: int,
) -> None:
    service = AdminCalendarService(session=session)
    calendar_month = await service.get_month(year=year, month=month)

    await state.update_data(
        admin_calendar_year=calendar_month.year,
        admin_calendar_month=calendar_month.month,
    )
    await state.set_state(AdminCalendarState.viewing_month)
    await message.answer(
        service.build_text(calendar_month),
        reply_markup=build_admin_calendar_inline_keyboard(
            weeks=calendar_month.weeks,
            year=calendar_month.year,
            month=calendar_month.month,
            previous_year=calendar_month.previous_year,
            previous_month=calendar_month.previous_month,
            next_year=calendar_month.next_year,
            next_month=calendar_month.next_month,
        ),
    )


async def _edit_admin_calendar_month(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    year: int,
    month: int,
) -> None:
    service = AdminCalendarService(session=session)
    calendar_month = await service.get_month(year=year, month=month)

    await state.update_data(
        admin_calendar_year=calendar_month.year,
        admin_calendar_month=calendar_month.month,
    )
    await state.set_state(AdminCalendarState.viewing_month)
    await callback.message.edit_text(
        service.build_text(calendar_month),
        reply_markup=build_admin_calendar_inline_keyboard(
            weeks=calendar_month.weeks,
            year=calendar_month.year,
            month=calendar_month.month,
            previous_year=calendar_month.previous_year,
            previous_month=calendar_month.previous_month,
            next_year=calendar_month.next_year,
            next_month=calendar_month.next_month,
        ),
    )
    await callback.answer()


async def _send_admin_calendar_day(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    appointment_date: date,
) -> None:
    service = AdminCalendarService(session=session)
    calendar_day = await service.get_day(appointment_date=appointment_date)
    appointment_buttons = {
        f"Открыть #{appointment.id}": appointment.id
        for appointment in calendar_day.appointments
    }

    await state.update_data(
        admin_calendar_date=appointment_date.isoformat(),
        admin_calendar_appointments=appointment_buttons,
        selected_admin_calendar_appointment_id=None,
    )
    await state.set_state(AdminCalendarState.viewing_day)
    await message.answer(
        calendar_day.text,
        reply_markup=build_admin_calendar_day_inline_keyboard(
            calendar_day.appointments,
            blocked_slot_texts=calendar_day.blocked_slot_texts,
            has_temporary_day_off=calendar_day.has_temporary_day_off,
            has_weekly_day_off=calendar_day.has_weekly_day_off,
        ),
    )


async def _edit_admin_calendar_day(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    appointment_date: date,
) -> None:
    service = AdminCalendarService(session=session)
    calendar_day = await service.get_day(appointment_date=appointment_date)
    appointment_buttons = {
        f"Открыть #{appointment.id}": appointment.id
        for appointment in calendar_day.appointments
    }

    await state.update_data(
        admin_calendar_date=appointment_date.isoformat(),
        admin_calendar_appointments=appointment_buttons,
        selected_admin_calendar_appointment_id=None,
    )
    await state.set_state(AdminCalendarState.viewing_day)
    await callback.message.edit_text(
        calendar_day.text,
        reply_markup=build_admin_calendar_day_inline_keyboard(
            calendar_day.appointments,
            blocked_slot_texts=calendar_day.blocked_slot_texts,
            has_temporary_day_off=calendar_day.has_temporary_day_off,
            has_weekly_day_off=calendar_day.has_weekly_day_off,
        ),
    )
    await callback.answer()


async def _send_admin_calendar_appointment_card(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    appointment_id: int,
) -> None:
    service = AdminAppointmentService(session=session)
    card_text = await service.get_appointment_card(appointment_id=appointment_id)

    if not card_text:
        await message.answer("Заявка не найдена.")
        return

    await state.update_data(selected_admin_calendar_appointment_id=appointment_id)
    await state.set_state(AdminCalendarState.viewing_appointment)
    await message.answer(
        card_text,
        reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
            appointment_id=appointment_id,
        ),
    )


async def _edit_admin_calendar_appointment_card(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    appointment_id: int,
) -> None:
    service = AdminAppointmentService(session=session)
    card_text = await service.get_appointment_card(appointment_id=appointment_id)

    if not card_text:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    await state.update_data(selected_admin_calendar_appointment_id=appointment_id)
    await state.set_state(AdminCalendarState.viewing_appointment)
    await callback.message.edit_text(
        card_text,
        reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
            appointment_id=appointment_id,
        ),
    )
    await callback.answer()


async def _send_client_contact(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    appointment_id = data.get("selected_admin_calendar_appointment_id")

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
        reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
            appointment_id=int(appointment_id),
        ),
    )


async def _handle_admin_appointment_action(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    action: str,
) -> None:
    data = await state.get_data()
    appointment_id = data.get("selected_admin_calendar_appointment_id")

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
            reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
                appointment_id=int(appointment_id),
            ),
        )
        return

    await state.clear()
    await message.answer(admin_message, reply_markup=master_menu_kb)


async def _handle_admin_calendar_appointment_action_callback(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    appointment_id: int,
    action: str,
) -> None:
    service = AdminAppointmentService(session=session)

    if action == "confirm":
        result = await service.confirm_appointment(appointment_id=appointment_id)
    else:
        result = await service.reject_appointment(appointment_id=appointment_id)

    notification_sent = await _send_client_notification(
        message=callback.message,
        chat_id=result.client_chat_id,
        text=result.client_message,
    )
    admin_message = result.admin_message

    if result.client_message and not notification_sent:
        admin_message += "\n\nНе удалось отправить уведомление клиенту."

    card_text = await service.get_appointment_card(appointment_id=appointment_id)

    if card_text:
        await callback.message.edit_text(
            admin_message + "\n\n" + card_text,
            reply_markup=build_admin_calendar_appointment_card_inline_keyboard(
                appointment_id=appointment_id,
            ),
        )
        await callback.answer()
        return

    await state.clear()
    await callback.message.answer(admin_message, reply_markup=master_menu_kb)
    await callback.answer()


async def _send_client_notification(
    message: Message,
    chat_id: int | None,
    text: str | None,
) -> bool:
    if not chat_id or not text:
        return False

    try:
        await message.bot.send_message(chat_id=chat_id, text=text)
    except (TelegramAPIError, TelegramNetworkError):
        return False

    return True


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)


def _callback_from_admin(session: AsyncSession, callback: CallbackQuery) -> bool:
    if not callback.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=callback.from_user.id)


async def _get_state_admin_calendar_date(state: FSMContext) -> date | None:
    state_data = await state.get_data()
    return _parse_state_date(state_data.get("admin_calendar_date"))


def _parse_state_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
