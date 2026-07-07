from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
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

router = Router()


@router.message(F.text == CLIENT_CALENDAR_BUTTON)
async def show_client_calendar(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    await message.answer(
        "Календарь мастера открыт.",
        reply_markup=build_back_main_keyboard(),
    )

    today = date.today()
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
    if message.text in {MAIN_MENU_BUTTON, "⬅️ Назад"}:
        await state.clear()
        await message.answer("Главное меню", reply_markup=client_menu_kb)
        return

    await message.answer("Используйте inline-кнопки календаря.")


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
        await _edit_client_calendar_month(
            session=session,
            callback=callback,
            state=state,
            year=int(parts[2]),
            month=int(parts[3]),
        )
        return

    if action == "day" and len(parts) == 3:
        appointment_date = date.fromisoformat(parts[2])
        service = AppointmentService(session=session)
        availability = await service.get_date_availability(
            appointment_date=appointment_date,
        )

        if not availability.available:
            await callback.answer(
                availability.message or "На эту дату свободных слотов нет.",
                show_alert=True,
            )
            return

        available_times = await service.get_available_time_texts(
            appointment_date=appointment_date,
        )

        if available_times:
            await callback.answer()
            await callback.message.answer(
                f"{appointment_date.strftime(DATE_FORMAT)}\n\n"
                "Свободные слоты:\n"
                + "\n".join(available_times)
                + "\n\nЗапись создаётся через карточку эскиза.",
                reply_markup=build_back_main_keyboard(),
            )
            return

        await callback.answer("На эту дату свободных слотов нет.", show_alert=True)
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
    return (
        f"Календарь мастера: {title}\n\n"
        "Можно посмотреть свободные слоты.\n"
        "Запись создаётся только через выбранный эскиз."
    )
