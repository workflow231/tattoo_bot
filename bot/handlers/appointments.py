from datetime import date, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CANCEL_BUTTON,
    CANCEL_APPOINTMENT_BUTTON,
    CATALOG_BUTTON,
    CHANGE_COMMENT_BUTTON,
    CHANGE_DATE_BUTTON,
    CHANGE_TIME_BUTTON,
    CHOOSE_SKETCH_BUTTON,
    CONFIRM_CREATE_REQUEST_BUTTON,
    CREATE_REQUEST_BUTTON,
    CHAT_WITH_MASTER_BUTTON,
    APPOINTMENT_NEXT_MONTH_BUTTON,
    APPOINTMENT_PREVIOUS_MONTH_BUTTON,
    APPOINTMENT_LIST_PAGE_SIZE,
    MAIN_MENU_BUTTON,
    MY_SKETCH_BUTTON,
    MY_APPOINTMENTS_BUTTON,
    NEXT_PAGE_BUTTON,
    NO_SKETCH_REQUEST_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    SEND_MY_SKETCH_BUTTON,
    SKIP_COMMENT_BUTTON,
    build_appointment_calendar_keyboard,
    build_appointment_comment_keyboard,
    build_appointment_confirm_keyboard,
    build_appointment_date_keyboard,
    build_appointment_time_keyboard,
    build_booking_menu_keyboard,
    build_custom_sketch_menu_keyboard,
    build_my_appointment_card_keyboard,
    build_my_appointments_keyboard,
    client_menu_kb,
    sketch_card_kb,
)
from bot.handlers.sketch_catalog_handler import start_sketch_catalog
from bot.menu_utils import get_main_menu_for_message
from bot.states import (
    AppointmentState,
    BookingState,
    MyAppointmentsState,
    SketchCatalogState,
)
from services.appointment_service import (
    TIME_FORMAT,
    AppointmentDraft,
    AppointmentService,
)
from services.client_text_service import ClientTextService
from services.master_contact_service import MasterContactService
from utils.timezone import today_in_bot_timezone

router = Router()


@router.message(F.text == CATALOG_BUTTON)
async def show_booking_menu(message: Message, state: FSMContext):
    await _send_booking_menu(message=message, state=state)


@router.message(BookingState.choosing_action)
async def choose_booking_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await state.clear()
        await message.answer(
            ClientTextService().text("main_menu"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == CHOOSE_SKETCH_BUTTON:
        await start_sketch_catalog(message=message, state=state, session=session)
        return

    if message.text == CHAT_WITH_MASTER_BUTTON:
        await message.answer(
            MasterContactService().get_contact_text(),
            reply_markup=build_booking_menu_keyboard(),
        )
        return

    if message.text == NO_SKETCH_REQUEST_BUTTON:
        await _start_appointment_date_selection(
            session=session,
            message=message,
            state=state,
            request_type="no_sketch",
        )
        return

    if message.text == MY_SKETCH_BUTTON:
        await _send_custom_sketch_menu(message=message, state=state)
        return

    await message.answer(
        ClientTextService().text("choose_action"),
        reply_markup=build_booking_menu_keyboard(),
    )


@router.message(BookingState.choosing_custom_sketch_action)
async def choose_custom_sketch_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await _send_booking_menu(message=message, state=state)
        return

    if message.text == CHAT_WITH_MASTER_BUTTON:
        await message.answer(
            MasterContactService().get_contact_text(),
            reply_markup=build_custom_sketch_menu_keyboard(),
        )
        return

    if message.text == SEND_MY_SKETCH_BUTTON:
        await state.set_state(BookingState.waiting_custom_sketch_photo)
        await message.answer(
            ClientTextService().text("custom_sketch_photo_prompt"),
            reply_markup=build_custom_sketch_menu_keyboard(),
        )
        return

    await message.answer(
        ClientTextService().text("choose_action"),
        reply_markup=build_custom_sketch_menu_keyboard(),
    )


@router.message(BookingState.waiting_custom_sketch_photo)
async def collect_custom_sketch_photo(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await _send_custom_sketch_menu(message=message, state=state)
        return

    if message.text == CHAT_WITH_MASTER_BUTTON:
        await message.answer(
            MasterContactService().get_contact_text(),
            reply_markup=build_custom_sketch_menu_keyboard(),
        )
        return

    if not message.photo:
        await message.answer(
            ClientTextService().text("custom_sketch_photo_required"),
            reply_markup=build_custom_sketch_menu_keyboard(),
        )
        return

    await _start_appointment_date_selection(
        session=session,
        message=message,
        state=state,
        request_type="custom_sketch",
        client_sketch_photo_file_id=message.photo[-1].file_id,
    )


@router.message(F.text == MY_APPOINTMENTS_BUTTON)
async def show_my_appointments(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    await _send_my_appointments_list(
        session=session,
        message=message,
        state=state,
    )


@router.message(MyAppointmentsState.choosing_appointment)
async def choose_my_appointment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    data = await state.get_data()
    appointment_buttons: dict[str, int] = data.get("appointment_buttons", {})

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_my_appointments_list(
            session=session,
            message=message,
            state=state,
            page=_shift_page(
                current_page=int(data.get("appointment_page", 0)),
                step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
                items_count=int(data.get("appointment_count", 0)),
            ),
        )
        return

    appointment_id = appointment_buttons.get(message.text or "")

    if not appointment_id or not message.from_user:
        await message.answer(ClientTextService().text("appointments_choose_from_list"))
        return

    service = AppointmentService(session=session)
    card_text = await service.get_current_user_appointment_card(
        telegram_id=message.from_user.id,
        appointment_id=appointment_id,
    )
    can_cancel = await service.can_cancel_current_user_appointment(
        telegram_id=message.from_user.id,
        appointment_id=appointment_id,
    )

    if not card_text:
        await message.answer(
            ClientTextService().text("appointment_not_found"),
            reply_markup=client_menu_kb,
        )
        await state.clear()
        return

    await state.update_data(selected_appointment_id=appointment_id)
    await state.set_state(MyAppointmentsState.viewing_appointment)
    await message.answer(
        card_text,
        reply_markup=build_my_appointment_card_keyboard(can_cancel=can_cancel),
    )


@router.message(MyAppointmentsState.viewing_appointment)
async def view_my_appointment_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        data = await state.get_data()
        await _send_my_appointments_list(
            session=session,
            message=message,
            state=state,
            page=int(data.get("appointment_page", 0)),
        )
        return

    if message.text == CHAT_WITH_MASTER_BUTTON:
        await message.answer(
            MasterContactService().get_contact_text(),
            reply_markup=await _build_current_my_appointment_keyboard(
                session=session,
                message=message,
                state=state,
            ),
        )
        return

    if message.text == CANCEL_APPOINTMENT_BUTTON:
        await _cancel_my_appointment(
            session=session,
            message=message,
            state=state,
        )
        return

    await message.answer(
        ClientTextService().text("choose_action"),
        reply_markup=await _build_current_my_appointment_keyboard(
            session=session,
            message=message,
            state=state,
        ),
    )


@router.message(SketchCatalogState.sketch_selected, F.text == CREATE_REQUEST_BUTTON)
async def start_appointment_creation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    data = await state.get_data()

    if not data.get("sketch_id"):
        await message.answer(
            ClientTextService().text("appointment_sketch_missing"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    await _start_appointment_date_selection(
        session=session,
        message=message,
        state=state,
        request_type="catalog_sketch",
        sketch_id=int(data["sketch_id"]),
        back_target="sketch_card",
    )


@router.message(AppointmentState.choosing_date)
async def choose_appointment_date(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await _handle_appointment_date_back(message=message, state=state)
        return

    data = await state.get_data()
    today = today_in_bot_timezone()
    year = int(data.get("appointment_calendar_year", today.year))
    month = int(data.get("appointment_calendar_month", today.month))
    service = AppointmentService(session=session)

    if message.text in {
        APPOINTMENT_PREVIOUS_MONTH_BUTTON,
        APPOINTMENT_NEXT_MONTH_BUTTON,
    }:
        step = -1 if message.text == APPOINTMENT_PREVIOUS_MONTH_BUTTON else 1
        year, month = service.shift_month(year=year, month=month, step=step)
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=date(year, month, 1),
        )
        return

    available_dates: dict[str, str] = data.get("appointment_available_dates", {})
    appointment_date = _parse_state_date(available_dates.get(message.text or ""))

    if not appointment_date:
        await message.answer(
            ClientTextService().text("appointment_choose_available_day"),
            reply_markup=build_appointment_calendar_keyboard(
                data.get("appointment_calendar_weeks", [])
            ),
        )
        return

    date_availability = await service.get_date_availability(
        appointment_date=appointment_date,
    )

    if not date_availability.available:
        await message.answer(
            date_availability.message
            or ClientTextService().text("appointment_date_unavailable"),
            reply_markup=build_appointment_calendar_keyboard(
                data.get("appointment_calendar_weeks", [])
            ),
        )
        return

    available_times = await service.get_available_time_texts(
        appointment_date=appointment_date,
    )

    if not available_times:
        await message.answer(
            ClientTextService().text("appointment_no_slots_for_date"),
            reply_markup=build_appointment_calendar_keyboard(
                data.get("appointment_calendar_weeks", [])
            ),
        )
        return

    await state.update_data(
        appointment_date=appointment_date.isoformat(),
        available_appointment_times=available_times,
        appointment_time=None,
    )
    await state.set_state(AppointmentState.choosing_time)
    await message.answer(
        ClientTextService().text("appointment_choose_time"),
        reply_markup=build_appointment_time_keyboard(available_times),
    )


@router.message(AppointmentState.choosing_time)
async def choose_appointment_time(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AppointmentState.choosing_date)
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=today_in_bot_timezone(),
        )
        return

    service = AppointmentService(session=session)
    appointment_time = service.parse_time(message.text or "")
    data = await state.get_data()
    available_times: list[str] = data.get("available_appointment_times", [])

    if not appointment_time or message.text not in available_times:
        await message.answer(
            ClientTextService().text("appointment_choose_time_button"),
            reply_markup=build_appointment_time_keyboard(available_times),
        )
        return

    await state.update_data(appointment_time=appointment_time.strftime(TIME_FORMAT))
    await state.set_state(AppointmentState.waiting_comment)
    await message.answer(
        ClientTextService().text("appointment_comment_prompt"),
        reply_markup=build_appointment_comment_keyboard(),
    )


@router.message(AppointmentState.waiting_comment)
async def collect_appointment_comment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AppointmentState.choosing_time)
        data = await state.get_data()
        available_times: list[str] = data.get("available_appointment_times", [])
        await message.answer(
            ClientTextService().text("appointment_choose_time"),
            reply_markup=build_appointment_time_keyboard(available_times),
        )
        return

    comment = None if message.text == SKIP_COMMENT_BUTTON else message.text
    await state.update_data(appointment_comment=comment)
    await _show_appointment_summary(
        session=session,
        message=message,
        state=state,
    )


@router.message(AppointmentState.confirming)
async def confirm_appointment_creation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state, session=session):
        return

    if message.text == CANCEL_BUTTON:
        await state.clear()
        await message.answer(
            ClientTextService().text("appointment_cancelled"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == CHANGE_DATE_BUTTON:
        await state.set_state(AppointmentState.choosing_date)
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=today_in_bot_timezone(),
        )
        return

    if message.text == CHANGE_TIME_BUTTON:
        data = await state.get_data()
        available_times = await _get_available_times_from_state(
            session=session,
            state_data=data,
        )

        if not available_times:
            await state.set_state(AppointmentState.choosing_date)
            await message.answer(
                ClientTextService().text("appointment_no_slots_for_date"),
                reply_markup=build_appointment_date_keyboard(),
            )
            return

        await state.update_data(available_appointment_times=available_times)
        await state.set_state(AppointmentState.choosing_time)
        await message.answer(
            ClientTextService().text("appointment_choose_time"),
            reply_markup=build_appointment_time_keyboard(available_times),
        )
        return

    if message.text == CHANGE_COMMENT_BUTTON:
        await state.set_state(AppointmentState.waiting_comment)
        await message.answer(
            ClientTextService().text("appointment_comment_prompt"),
            reply_markup=build_appointment_comment_keyboard(),
        )
        return

    if message.text != CONFIRM_CREATE_REQUEST_BUTTON:
        await message.answer(
            ClientTextService().text("choose_action"),
            reply_markup=build_appointment_confirm_keyboard(),
        )
        return

    service = AppointmentService(session=session)
    draft = _build_draft_from_state(await state.get_data())

    if not draft or not message.from_user:
        await message.answer(
            ClientTextService().text("appointment_create_missing_data")
        )
        return

    appointment = await service.create_pending_appointment(
        telegram_id=message.from_user.id,
        draft=draft,
    )

    if not appointment:
        await message.answer(
            ClientTextService().text("appointment_create_failed"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    await state.clear()
    await message.answer(
        ClientTextService().appointment_created(),
        reply_markup=get_main_menu_for_message(session=session, message=message),
    )


async def _show_appointment_summary(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    service = AppointmentService(session=session)
    data = await state.get_data()
    draft = _build_draft_from_state(data)

    if not draft:
        await state.set_state(AppointmentState.choosing_date)
        await message.answer(ClientTextService().text("appointment_missing_data"))
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=today_in_bot_timezone(),
        )
        return

    sketch = None

    if draft.request_type == "catalog_sketch" and draft.sketch_id:
        sketch = await service.get_sketch(sketch_id=draft.sketch_id)

    if draft.request_type == "catalog_sketch" and not sketch:
        await state.clear()
        await message.answer(
            ClientTextService().text("appointment_sketch_unavailable"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    await state.set_state(AppointmentState.confirming)
    await message.answer(
        service.build_summary_text(sketch=sketch, draft=draft),
        reply_markup=build_appointment_confirm_keyboard(),
    )


async def _send_my_appointments_list(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    page: int = 0,
) -> None:
    if not message.from_user:
        await message.answer(
            ClientTextService().text("user_unknown"), reply_markup=client_menu_kb
        )
        return

    service = AppointmentService(session=session)
    appointments = await service.list_current_user_appointments(
        telegram_id=message.from_user.id,
    )

    if not appointments:
        await state.clear()
        await message.answer(
            ClientTextService().text("appointments_empty"),
            reply_markup=client_menu_kb,
        )
        return

    page = _normalize_page(page=page, items_count=len(appointments))
    page_appointments = _get_page_items(appointments, page=page)
    appointment_buttons = {
        f"Заявка #{appointment.id}": appointment.id for appointment in page_appointments
    }

    await state.update_data(
        appointment_buttons=appointment_buttons,
        appointment_page=page,
        appointment_count=len(appointments),
    )
    await state.set_state(MyAppointmentsState.choosing_appointment)
    await message.answer(
        ClientTextService().format_text(
            "appointments_list",
            appointments=_build_paginated_list_text(
                items=[appointment.text for appointment in page_appointments],
                page=page,
                items_count=len(appointments),
            ),
        ),
        reply_markup=build_my_appointments_keyboard(appointments, page=page),
    )


async def _cancel_my_appointment(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    if not message.from_user:
        await message.answer(
            ClientTextService().text("user_unknown"), reply_markup=client_menu_kb
        )
        return

    data = await state.get_data()
    appointment_id = data.get("selected_appointment_id")

    if not appointment_id:
        await state.clear()
        await message.answer(
            ClientTextService().text("appointment_not_selected"),
            reply_markup=client_menu_kb,
        )
        return

    service = AppointmentService(session=session)
    result_text = await service.cancel_current_user_appointment(
        telegram_id=message.from_user.id,
        appointment_id=int(appointment_id),
    )

    if not result_text:
        await state.clear()
        await message.answer(
            ClientTextService().text("appointment_not_found"),
            reply_markup=client_menu_kb,
        )
        return

    card_text = await service.get_current_user_appointment_card(
        telegram_id=message.from_user.id,
        appointment_id=int(appointment_id),
    )

    if not card_text:
        await state.clear()
        await message.answer(result_text, reply_markup=client_menu_kb)
        return

    await message.answer(
        f"{result_text}\n\n{card_text}",
        reply_markup=build_my_appointment_card_keyboard(can_cancel=False),
    )


async def _build_current_my_appointment_keyboard(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
):
    if not message.from_user:
        return build_my_appointment_card_keyboard()

    data = await state.get_data()
    appointment_id = data.get("selected_appointment_id")

    if not appointment_id:
        return build_my_appointment_card_keyboard()

    service = AppointmentService(session=session)
    can_cancel = await service.can_cancel_current_user_appointment(
        telegram_id=message.from_user.id,
        appointment_id=int(appointment_id),
    )
    return build_my_appointment_card_keyboard(can_cancel=can_cancel)


async def _send_appointment_calendar(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    target_date: date,
) -> None:
    service = AppointmentService(session=session)
    calendar_month = await service.get_calendar_month(
        year=target_date.year,
        month=target_date.month,
    )

    await state.update_data(
        appointment_calendar_year=calendar_month.year,
        appointment_calendar_month=calendar_month.month,
        appointment_calendar_weeks=calendar_month.weeks,
        appointment_available_dates=calendar_month.available_dates,
    )
    await message.answer(
        ClientTextService().format_text(
            "appointment_choose_date",
            month_title=calendar_month.title,
        ),
        reply_markup=build_appointment_calendar_keyboard(calendar_month.weeks),
    )


async def _start_appointment_date_selection(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    request_type: str,
    sketch_id: int | None = None,
    client_sketch_photo_file_id: str | None = None,
    back_target: str | None = None,
) -> None:
    await state.update_data(
        sketch_id=sketch_id,
        appointment_request_type=request_type,
        client_sketch_photo_file_id=client_sketch_photo_file_id,
        appointment_back_target=back_target or request_type,
    )
    await state.set_state(AppointmentState.choosing_date)
    await _send_appointment_calendar(
        session=session,
        message=message,
        state=state,
        target_date=today_in_bot_timezone(),
    )


async def _send_booking_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingState.choosing_action)
    await message.answer(
        ClientTextService().text("booking_menu_prompt"),
        reply_markup=build_booking_menu_keyboard(),
    )


async def _send_custom_sketch_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingState.choosing_custom_sketch_action)
    await message.answer(
        ClientTextService().text("custom_sketch_menu_prompt"),
        reply_markup=build_custom_sketch_menu_keyboard(),
    )


async def _handle_appointment_date_back(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    back_target = data.get("appointment_back_target")

    if back_target == "sketch_card":
        await state.set_state(SketchCatalogState.sketch_selected)
        await message.answer(
            ClientTextService().text("appointment_back_to_sketch_card"),
            reply_markup=sketch_card_kb,
        )
        return

    if back_target == "custom_sketch":
        await _send_custom_sketch_menu(message=message, state=state)
        return

    await _send_booking_menu(message=message, state=state)


async def _handle_common_navigation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> bool:
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer(
            ClientTextService().text("main_menu"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return True

    return False


async def _get_available_times_from_state(
    session: AsyncSession,
    state_data: dict,
) -> list[str]:
    appointment_date = _parse_state_date(state_data.get("appointment_date"))

    if not appointment_date:
        return []

    service = AppointmentService(session=session)
    return await service.get_available_time_texts(appointment_date=appointment_date)


def _build_draft_from_state(data: dict) -> AppointmentDraft | None:
    sketch_id = data.get("sketch_id")
    appointment_date = _parse_state_date(data.get("appointment_date"))
    appointment_time = _parse_state_time(data.get("appointment_time"))
    request_type = data.get("appointment_request_type", "catalog_sketch")

    if not appointment_date or not appointment_time:
        return None

    if request_type == "catalog_sketch" and not sketch_id:
        return None

    return AppointmentDraft(
        sketch_id=int(sketch_id) if sketch_id else None,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        comment=data.get("appointment_comment"),
        request_type=request_type,
        client_sketch_photo_file_id=data.get("client_sketch_photo_file_id"),
    )


def _parse_state_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_state_time(value: str | None) -> time | None:
    if not value:
        return None

    try:
        return time.fromisoformat(value)
    except ValueError:
        return None


def _get_page_items(items, page: int):
    start = page * APPOINTMENT_LIST_PAGE_SIZE
    return items[start : start + APPOINTMENT_LIST_PAGE_SIZE]


def _normalize_page(page: int, items_count: int) -> int:
    last_page = max((items_count - 1) // APPOINTMENT_LIST_PAGE_SIZE, 0)
    return min(max(page, 0), last_page)


def _shift_page(current_page: int, step: int, items_count: int) -> int:
    return _normalize_page(page=current_page + step, items_count=items_count)


def _build_paginated_list_text(
    items: list[str],
    page: int,
    items_count: int,
) -> str:
    last_page = max((items_count - 1) // APPOINTMENT_LIST_PAGE_SIZE, 0)

    if last_page == 0:
        return "\n".join(items)

    return f"Страница {page + 1} из {last_page + 1}\n" + "\n".join(items)
