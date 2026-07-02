from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    ADMIN_ADD_DAY_OFF_BUTTON,
    ADMIN_APPROVE_APPOINTMENT_BUTTON,
    ADMIN_BACK_TO_CALENDAR_BUTTON,
    ADMIN_BACK_TO_CALENDAR_DAY_BUTTON,
    ADMIN_BLOCK_SLOT_BUTTON,
    ADMIN_NEXT_MONTH_BUTTON,
    ADMIN_PREVIOUS_MONTH_BUTTON,
    ADMIN_REJECT_APPOINTMENT_BUTTON,
    ADMIN_REMOVE_TEMPORARY_DAY_OFF_BUTTON,
    ADMIN_REMOVE_WEEKLY_DAY_OFF_BUTTON,
    ADMIN_REMOVE_BLOCKED_SLOT_PREFIX,
    ADMIN_TEMPORARY_DAY_OFF_BUTTON,
    ADMIN_WRITE_CLIENT_BUTTON,
    ADMIN_WEEKLY_DAY_OFF_BUTTON,
    CALENDAR_BUTTON,
    CANCEL_BUTTON,
    MAIN_MENU_BUTTON,
    build_admin_calendar_appointment_card_keyboard,
    build_admin_calendar_day_keyboard,
    build_admin_calendar_keyboard,
    build_admin_day_off_type_keyboard,
    build_admin_slot_keyboard,
    menu_kb,
)
from bot.states import AdminCalendarState
from services.admin_appointment_service import AdminAppointmentService
from services.admin_calendar_service import AdminCalendarService

router = Router()


@router.message(F.text == CALENDAR_BUTTON)
async def show_admin_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    today = date.today()
    await _send_admin_calendar_month(
        session=session,
        message=message,
        state=state,
        year=today.year,
        month=today.month,
    )


@router.message(AdminCalendarState.viewing_month)
async def navigate_admin_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    data = await state.get_data()
    year = int(data.get("admin_calendar_year", date.today().year))
    month = int(data.get("admin_calendar_month", date.today().month))
    service = AdminCalendarService(session=session)

    if message.text == ADMIN_PREVIOUS_MONTH_BUTTON:
        year, month = service.shift_month(year=year, month=month, step=-1)
    elif message.text == ADMIN_NEXT_MONTH_BUTTON:
        year, month = service.shift_month(year=year, month=month, step=1)
    else:
        appointment_date = service.parse_day_label(
            value=message.text,
            year=year,
            month=month,
        )

        if appointment_date:
            await _send_admin_calendar_day(
                session=session,
                message=message,
                state=state,
                appointment_date=appointment_date,
            )
            return

        await message.answer(
            "Выберите день или месяц кнопкой навигации.",
            reply_markup=build_admin_calendar_keyboard(
                (await service.get_month(year=year, month=month)).weeks,
            ),
        )
        return

    await _send_admin_calendar_month(
        session=session,
        message=message,
        state=state,
        year=year,
        month=month,
    )


@router.message(AdminCalendarState.viewing_day)
async def view_admin_calendar_day(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.set_state(AdminCalendarState.viewing_month)
        await message.answer("Дата не выбрана.", reply_markup=menu_kb)
        return

    if message.text == ADMIN_BACK_TO_CALENDAR_BUTTON:
        await _send_admin_calendar_month(
            session=session,
            message=message,
            state=state,
            year=appointment_date.year,
            month=appointment_date.month,
        )
        return

    if message.text == ADMIN_ADD_DAY_OFF_BUTTON:
        await state.set_state(AdminCalendarState.choosing_day_off_type)
        await message.answer(
            "Какой выходной добавить?",
            reply_markup=build_admin_day_off_type_keyboard(),
        )
        return

    if message.text == ADMIN_BLOCK_SLOT_BUTTON:
        await state.set_state(AdminCalendarState.choosing_slot)
        await message.answer(
            "Выберите слот для блокировки:",
            reply_markup=build_admin_slot_keyboard(),
        )
        return

    if message.text == ADMIN_REMOVE_TEMPORARY_DAY_OFF_BUTTON:
        service = AdminCalendarService(session=session)
        result_text = await service.remove_temporary_day_off(
            appointment_date=appointment_date,
        )
        await message.answer(result_text)
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    if message.text == ADMIN_REMOVE_WEEKLY_DAY_OFF_BUTTON:
        service = AdminCalendarService(session=session)
        result_text = await service.remove_weekly_day_off(
            appointment_date=appointment_date,
        )
        await message.answer(result_text)
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    if (message.text or "").startswith(ADMIN_REMOVE_BLOCKED_SLOT_PREFIX):
        time_text = (
            (message.text or "")
            .replace(
                ADMIN_REMOVE_BLOCKED_SLOT_PREFIX,
                "",
                1,
            )
            .strip()
        )
        service = AdminCalendarService(session=session)
        result_text = await service.remove_blocked_slot(
            appointment_date=appointment_date,
            time_text=time_text,
        )

        if not result_text:
            await message.answer("Выберите блокировку кнопкой из списка.")
            return

        await message.answer(result_text)
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    appointment_buttons: dict[str, int] = data.get("admin_calendar_appointments", {})
    appointment_id = appointment_buttons.get(message.text or "")

    if not appointment_id:
        await message.answer("Выберите заявку кнопкой из списка.")
        return

    await _send_admin_calendar_appointment_card(
        session=session,
        message=message,
        state=state,
        appointment_id=appointment_id,
    )


@router.message(AdminCalendarState.choosing_slot)
async def choose_admin_blocked_slot(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.clear()
        await message.answer("Дата не выбрана.", reply_markup=menu_kb)
        return

    if message.text == CANCEL_BUTTON:
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    service = AdminCalendarService(session=session)
    result_text = await service.add_blocked_slot(
        appointment_date=appointment_date,
        time_text=message.text or "",
    )

    if not result_text:
        await message.answer(
            "Выберите слот кнопкой.",
            reply_markup=build_admin_slot_keyboard(),
        )
        return

    await message.answer(result_text)
    await _send_admin_calendar_day(
        session=session,
        message=message,
        state=state,
        appointment_date=appointment_date,
    )


@router.message(AdminCalendarState.choosing_day_off_type)
async def choose_admin_day_off_type(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    data = await state.get_data()
    appointment_date = _parse_state_date(data.get("admin_calendar_date"))

    if not appointment_date:
        await state.clear()
        await message.answer("Дата не выбрана.", reply_markup=menu_kb)
        return

    if message.text == CANCEL_BUTTON:
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    if message.text == ADMIN_WEEKLY_DAY_OFF_BUTTON:
        service = AdminCalendarService(session=session)
        result_text = await service.add_weekly_day_off(
            appointment_date=appointment_date,
        )
        await message.answer(result_text)
        await _send_admin_calendar_day(
            session=session,
            message=message,
            state=state,
            appointment_date=appointment_date,
        )
        return

    if message.text != ADMIN_TEMPORARY_DAY_OFF_BUTTON:
        await message.answer(
            "Выберите тип выходного кнопкой.",
            reply_markup=build_admin_day_off_type_keyboard(),
        )
        return

    service = AdminCalendarService(session=session)
    result_text = await service.add_temporary_day_off(
        appointment_date=appointment_date,
    )
    await message.answer(result_text)
    await _send_admin_calendar_day(
        session=session,
        message=message,
        state=state,
        appointment_date=appointment_date,
    )


@router.message(AdminCalendarState.viewing_appointment)
async def view_admin_calendar_appointment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.", reply_markup=menu_kb)
        return

    if message.text == ADMIN_BACK_TO_CALENDAR_DAY_BUTTON:
        data = await state.get_data()
        appointment_date = _parse_state_date(data.get("admin_calendar_date"))

        if not appointment_date:
            await state.clear()
            await message.answer("Дата не выбрана.", reply_markup=menu_kb)
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

    await message.answer(
        "Выберите действие кнопкой.",
        reply_markup=build_admin_calendar_appointment_card_keyboard(),
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
        reply_markup=build_admin_calendar_keyboard(calendar_month.weeks),
    )


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
        reply_markup=build_admin_calendar_day_keyboard(
            calendar_day.appointments,
            blocked_slot_texts=calendar_day.blocked_slot_texts,
            has_temporary_day_off=calendar_day.has_temporary_day_off,
            has_weekly_day_off=calendar_day.has_weekly_day_off,
        ),
    )


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
        reply_markup=build_admin_calendar_appointment_card_keyboard(),
    )


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
        reply_markup=build_admin_calendar_appointment_card_keyboard(),
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
            reply_markup=build_admin_calendar_appointment_card_keyboard(),
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


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)


def _parse_state_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
