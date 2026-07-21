from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CLIENT_CALENDAR_BUTTON,
    CLIENT_CALENDAR_CALLBACK_PREFIX,
    CLIENT_CALENDAR_IGNORE_CALLBACK,
    MAIN_MENU_BUTTON,
    build_back_main_keyboard,
    build_client_calendar_inline_keyboard,
    client_menu_kb,
)
from bot.states import ClientCalendarState
from services.appointment_service import DATE_FORMAT, AppointmentService
from services.client_text_service import ClientTextService
from utils.timezone import today_in_bot_timezone

router = Router()


@router.message(F.text == CLIENT_CALENDAR_BUTTON)
async def show_client_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    await message.answer(
        ClientTextService().text("client_calendar_opened"),
        reply_markup=build_back_main_keyboard(),
    )

    today = today_in_bot_timezone()
    await _send_client_calendar_month(
        session=session,
        message=message,
        state=state,
        year=today.year,
        month=today.month,
    )


@router.message(ClientCalendarState.viewing_month)
async def client_calendar_navigation(
    message: Message,
    state: FSMContext,
):
    if message.text in {MAIN_MENU_BUTTON, BACK_BUTTON}:
        await state.clear()
        await message.answer(
            ClientTextService().text("main_menu"),
            reply_markup=client_menu_kb,
        )
        return

    await message.answer(ClientTextService().text("client_calendar_use_inline_buttons"))


@router.callback_query(F.data.startswith(f"{CLIENT_CALENDAR_CALLBACK_PREFIX}:"))
async def handle_client_calendar_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    if not callback.message:
        await callback.answer()
        return

    data = callback.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "month" and len(parts) == 4:
        calendar_month = _parse_callback_month(parts[2], parts[3])

        if not calendar_month:
            await _answer_invalid_client_calendar_callback(callback)
            return

        year, month = calendar_month
        await _edit_client_calendar_month(
            session=session,
            callback=callback,
            state=state,
            year=year,
            month=month,
        )
        return

    if action == "day" and len(parts) == 3:
        appointment_date = _parse_callback_date(parts[2])

        if not appointment_date:
            await _answer_invalid_client_calendar_callback(callback)
            return

        service = AppointmentService(session=session)
        availability = await service.get_date_availability(
            appointment_date=appointment_date,
        )

        if not availability.available:
            await callback.answer(
                availability.message
                or ClientTextService().text("client_calendar_no_slots"),
                show_alert=True,
            )
            return

        available_times = await service.get_available_time_texts(
            appointment_date=appointment_date,
        )

        if available_times:
            await callback.answer()
            await callback.message.answer(
                ClientTextService().format_text(
                    "client_calendar_day_slots",
                    appointment_date=appointment_date.strftime(DATE_FORMAT),
                    available_times="\n".join(available_times),
                ),
                reply_markup=build_back_main_keyboard(),
            )
            return

        await callback.answer(
            ClientTextService().text("client_calendar_no_slots"),
            show_alert=True,
        )
        return

    if action in {"month", "day"}:
        await _answer_invalid_client_calendar_callback(callback)
        return

    await callback.answer()


@router.callback_query(F.data == CLIENT_CALENDAR_IGNORE_CALLBACK)
async def ignore_client_calendar_callback(callback: CallbackQuery) -> None:
    await callback.answer()


async def _send_client_calendar_month(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    year: int,
    month: int,
) -> None:
    service = AppointmentService(session=session)
    calendar_month = await service.get_calendar_month(year=year, month=month)

    await state.update_data(
        client_calendar_year=calendar_month.year,
        client_calendar_month=calendar_month.month,
    )
    await state.set_state(ClientCalendarState.viewing_month)
    await message.answer(
        _build_client_calendar_text(calendar_month.title),
        reply_markup=build_client_calendar_inline_keyboard(
            weeks=calendar_month.weeks,
            year=calendar_month.year,
            month=calendar_month.month,
            previous_year=calendar_month.previous_year,
            previous_month=calendar_month.previous_month,
            next_year=calendar_month.next_year,
            next_month=calendar_month.next_month,
        ),
    )


async def _edit_client_calendar_month(
    session: AsyncSession,
    callback: CallbackQuery,
    state: FSMContext,
    year: int,
    month: int,
) -> None:
    service = AppointmentService(session=session)
    calendar_month = await service.get_calendar_month(year=year, month=month)

    await state.update_data(
        client_calendar_year=calendar_month.year,
        client_calendar_month=calendar_month.month,
    )
    await state.set_state(ClientCalendarState.viewing_month)
    await callback.message.edit_text(
        _build_client_calendar_text(calendar_month.title),
        reply_markup=build_client_calendar_inline_keyboard(
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


def _build_client_calendar_text(title: str) -> str:
    return ClientTextService().format_text(
        "client_calendar_month",
        month_title=title,
    )


async def _answer_invalid_client_calendar_callback(callback: CallbackQuery) -> None:
    await callback.answer(
        ClientTextService().stale_session(),
        show_alert=True,
    )


def _parse_callback_month(year_text: str, month_text: str) -> tuple[int, int] | None:
    try:
        year = int(year_text)
        month = int(month_text)
        date(year, month, 1)
    except ValueError:
        return None

    return year, month


def _parse_callback_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
