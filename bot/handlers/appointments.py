from datetime import date, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CANCEL_BUTTON,
    CANCEL_APPOINTMENT_BUTTON,
    CHANGE_COMMENT_BUTTON,
    CHANGE_DATE_BUTTON,
    CHANGE_TIME_BUTTON,
    CONFIRM_CREATE_REQUEST_BUTTON,
    CREATE_REQUEST_BUTTON,
    CHAT_WITH_MASTER_BUTTON,
    APPOINTMENT_NEXT_MONTH_BUTTON,
    APPOINTMENT_PREVIOUS_MONTH_BUTTON,
    MAIN_MENU_BUTTON,
    MY_APPOINTMENTS_BUTTON,
    SKIP_COMMENT_BUTTON,
    build_appointment_calendar_keyboard,
    build_appointment_comment_keyboard,
    build_appointment_confirm_keyboard,
    build_appointment_date_keyboard,
    build_appointment_time_keyboard,
    build_my_appointment_card_keyboard,
    build_my_appointments_keyboard,
    client_menu_kb,
    sketch_card_kb,
)
from bot.states import AppointmentState, MyAppointmentsState, SketchCatalogState
from services.appointment_service import (
    TIME_FORMAT,
    AppointmentDraft,
    AppointmentService,
)
from services.client_text_service import ClientTextService
from services.master_contact_service import MasterContactService

router = Router()


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
    if await _handle_common_navigation(message=message, state=state):
        return

    data = await state.get_data()
    appointment_buttons: dict[str, int] = data.get("appointment_buttons", {})
    appointment_id = appointment_buttons.get(message.text or "")

    if not appointment_id or not message.from_user:
        await message.answer("Выберите заявку кнопкой из списка.")
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
        await message.answer("Заявка не найдена.", reply_markup=client_menu_kb)
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
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await _send_my_appointments_list(
            session=session,
            message=message,
            state=state,
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
        "Выберите действие кнопкой.",
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
            "Сначала выберите эскиз из каталога.",
            reply_markup=client_menu_kb,
        )
        return

    await state.set_state(AppointmentState.choosing_date)
    await _send_appointment_calendar(
        session=session,
        message=message,
        state=state,
        target_date=date.today(),
    )


@router.message(AppointmentState.choosing_date)
async def choose_appointment_date(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(SketchCatalogState.sketch_selected)
        await message.answer(
            "Вы вернулись к карточке эскиза.",
            reply_markup=sketch_card_kb,
        )
        return

    data = await state.get_data()
    year = int(data.get("appointment_calendar_year", date.today().year))
    month = int(data.get("appointment_calendar_month", date.today().month))
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
            "Выберите доступный день в календаре.",
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
            date_availability.message or "Этот день недоступен. Выберите другую дату.",
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
            "На эту дату нет свободных слотов. Выберите другую дату.",
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
        "Выберите время:",
        reply_markup=build_appointment_time_keyboard(available_times),
    )


@router.message(AppointmentState.choosing_time)
async def choose_appointment_time(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AppointmentState.choosing_date)
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=date.today(),
        )
        return

    service = AppointmentService(session=session)
    appointment_time = service.parse_time(message.text or "")
    data = await state.get_data()
    available_times: list[str] = data.get("available_appointment_times", [])

    if not appointment_time or message.text not in available_times:
        await message.answer(
            "Выберите время кнопкой из списка.",
            reply_markup=build_appointment_time_keyboard(available_times),
        )
        return

    await state.update_data(appointment_time=appointment_time.strftime(TIME_FORMAT))
    await state.set_state(AppointmentState.waiting_comment)
    await message.answer(
        "Оставьте комментарий к заявке или нажмите «Пропустить».",
        reply_markup=build_appointment_comment_keyboard(),
    )


@router.message(AppointmentState.waiting_comment)
async def collect_appointment_comment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AppointmentState.choosing_time)
        data = await state.get_data()
        available_times: list[str] = data.get("available_appointment_times", [])
        await message.answer(
            "Выберите время:",
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
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == CANCEL_BUTTON:
        await state.clear()
        await message.answer("Создание заявки отменено.", reply_markup=client_menu_kb)
        return

    if message.text == CHANGE_DATE_BUTTON:
        await state.set_state(AppointmentState.choosing_date)
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=date.today(),
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
                "На выбранную дату больше нет свободных слотов. Введите другую дату.",
                reply_markup=build_appointment_date_keyboard(),
            )
            return

        await state.update_data(available_appointment_times=available_times)
        await state.set_state(AppointmentState.choosing_time)
        await message.answer(
            "Выберите время:",
            reply_markup=build_appointment_time_keyboard(available_times),
        )
        return

    if message.text == CHANGE_COMMENT_BUTTON:
        await state.set_state(AppointmentState.waiting_comment)
        await message.answer(
            "Оставьте комментарий к заявке или нажмите «Пропустить».",
            reply_markup=build_appointment_comment_keyboard(),
        )
        return

    if message.text != CONFIRM_CREATE_REQUEST_BUTTON:
        await message.answer(
            "Выберите действие кнопкой.",
            reply_markup=build_appointment_confirm_keyboard(),
        )
        return

    service = AppointmentService(session=session)
    draft = _build_draft_from_state(await state.get_data())

    if not draft or not message.from_user:
        await message.answer("Не удалось создать заявку. Попробуйте заново.")
        return

    appointment = await service.create_pending_appointment(
        telegram_id=message.from_user.id,
        draft=draft,
    )

    if not appointment:
        await message.answer(
            "Не удалось создать заявку. Возможно, эскиз недоступен или слот уже занят.",
            reply_markup=client_menu_kb,
        )
        return

    await state.clear()
    await message.answer(
        ClientTextService().appointment_created(),
        reply_markup=client_menu_kb,
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
        await message.answer("Не хватает данных для заявки. Выберите дату заново.")
        await _send_appointment_calendar(
            session=session,
            message=message,
            state=state,
            target_date=date.today(),
        )
        return

    sketch = await service.get_sketch(sketch_id=draft.sketch_id)

    if not sketch:
        await state.clear()
        await message.answer(
            "Эскиз не найден или уже недоступен.",
            reply_markup=client_menu_kb,
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
) -> None:
    if not message.from_user:
        await message.answer(
            "Не удалось определить пользователя.", reply_markup=client_menu_kb
        )
        return

    service = AppointmentService(session=session)
    appointments = await service.list_current_user_appointments(
        telegram_id=message.from_user.id,
    )

    if not appointments:
        await state.clear()
        await message.answer("У вас пока нет заявок.", reply_markup=client_menu_kb)
        return

    appointment_buttons = {
        f"Заявка #{appointment.id}": appointment.id for appointment in appointments
    }

    await state.update_data(appointment_buttons=appointment_buttons)
    await state.set_state(MyAppointmentsState.choosing_appointment)
    await message.answer(
        "Ваши заявки:\n\n"
        + "\n".join(appointment.text for appointment in appointments),
        reply_markup=build_my_appointments_keyboard(appointments),
    )


async def _cancel_my_appointment(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    if not message.from_user:
        await message.answer(
            "Не удалось определить пользователя.", reply_markup=client_menu_kb
        )
        return

    data = await state.get_data()
    appointment_id = data.get("selected_appointment_id")

    if not appointment_id:
        await state.clear()
        await message.answer("Заявка не выбрана.", reply_markup=client_menu_kb)
        return

    service = AppointmentService(session=session)
    result_text = await service.cancel_current_user_appointment(
        telegram_id=message.from_user.id,
        appointment_id=int(appointment_id),
    )

    if not result_text:
        await state.clear()
        await message.answer("Заявка не найдена.", reply_markup=client_menu_kb)
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
        f"Выберите дату: {calendar_month.title}\n\n"
        "Недоступные дни отмечены символом ×.",
        reply_markup=build_appointment_calendar_keyboard(calendar_month.weeks),
    )


async def _handle_common_navigation(
    message: Message,
    state: FSMContext,
) -> bool:
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=client_menu_kb)
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

    if not sketch_id or not appointment_date or not appointment_time:
        return None

    return AppointmentDraft(
        sketch_id=int(sketch_id),
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        comment=data.get("appointment_comment"),
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
