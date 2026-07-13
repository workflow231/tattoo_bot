from datetime import date, time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    MAIN_MENU_BUTTON,
    REMOVE_TEMPORARY_WORKING_HOURS_BUTTON,
    REMOVE_WEEKLY_WORKING_HOURS_BUTTON,
    SET_TEMPORARY_DAY_OFF_BUTTON,
    SET_TEMPORARY_WORKING_HOURS_BUTTON,
    SET_WEEKLY_DAY_OFF_BUTTON,
    SET_WEEKLY_WORKING_HOURS_BUTTON,
    SHOW_WORKING_HOURS_RULES_BUTTON,
    WORKING_HOURS_BUTTON,
    build_back_main_keyboard,
    build_weekday_keyboard,
    build_working_hours_actions_keyboard,
    master_menu_kb,
)
from bot.states import AdminWorkingHoursState
from services.admin_appointment_service import AdminAppointmentService
from services.working_hours_service import WorkingHoursService

router = Router()

ACTION_WEEKLY_DAY_OFF = "weekly_day_off"
ACTION_SHOW_RULES = "show_rules"
ACTION_WEEKLY_WORKING_HOURS = "weekly_working_hours"
ACTION_REMOVE_WEEKLY_WORKING_HOURS = "remove_weekly_working_hours"
ACTION_TEMPORARY_DAY_OFF = "temporary_day_off"
ACTION_TEMPORARY_WORKING_HOURS = "temporary_working_hours"
ACTION_REMOVE_TEMPORARY_WORKING_HOURS = "remove_temporary_working_hours"


@router.message(F.text == WORKING_HOURS_BUTTON)
async def show_working_hours_menu(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.")
        return

    await _send_actions_menu(message=message, state=state)


@router.message(AdminWorkingHoursState.choosing_action)
async def choose_working_hours_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    action_by_text = {
        SHOW_WORKING_HOURS_RULES_BUTTON: ACTION_SHOW_RULES,
        SET_WEEKLY_DAY_OFF_BUTTON: ACTION_WEEKLY_DAY_OFF,
        SET_WEEKLY_WORKING_HOURS_BUTTON: ACTION_WEEKLY_WORKING_HOURS,
        REMOVE_WEEKLY_WORKING_HOURS_BUTTON: ACTION_REMOVE_WEEKLY_WORKING_HOURS,
        SET_TEMPORARY_DAY_OFF_BUTTON: ACTION_TEMPORARY_DAY_OFF,
        SET_TEMPORARY_WORKING_HOURS_BUTTON: ACTION_TEMPORARY_WORKING_HOURS,
        REMOVE_TEMPORARY_WORKING_HOURS_BUTTON: ACTION_REMOVE_TEMPORARY_WORKING_HOURS,
    }
    action = action_by_text.get(message.text or "")

    if not action:
        await message.answer(
            "Выберите действие кнопкой.",
            reply_markup=build_working_hours_actions_keyboard(),
        )
        return

    await state.update_data(working_hours_action=action)

    if action == ACTION_SHOW_RULES:
        await message.answer(
            await WorkingHoursService(session=session).get_rules_text(),
            reply_markup=build_working_hours_actions_keyboard(),
        )
        return

    if action in {
        ACTION_WEEKLY_DAY_OFF,
        ACTION_WEEKLY_WORKING_HOURS,
        ACTION_REMOVE_WEEKLY_WORKING_HOURS,
    }:
        await state.set_state(AdminWorkingHoursState.choosing_weekday)
        await message.answer(
            "Выберите день недели:", reply_markup=build_weekday_keyboard()
        )
        return

    await state.set_state(AdminWorkingHoursState.waiting_date)
    await message.answer(
        "Введите дату в формате ДД.ММ.ГГГГ:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminWorkingHoursState.choosing_weekday)
async def choose_working_hours_weekday(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await _send_actions_menu(message=message, state=state)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = WorkingHoursService(session=session)
    weekday = service.parse_weekday(message.text)

    if weekday is None:
        await message.answer(
            "Выберите день недели кнопкой.", reply_markup=build_weekday_keyboard()
        )
        return

    data = await state.get_data()
    action = data.get("working_hours_action")

    if action == ACTION_WEEKLY_DAY_OFF:
        await message.answer(
            await service.add_weekly_day_off(weekday=weekday),
            reply_markup=build_working_hours_actions_keyboard(),
        )
        await state.set_state(AdminWorkingHoursState.choosing_action)
        return

    if action == ACTION_REMOVE_WEEKLY_WORKING_HOURS:
        await message.answer(
            await service.remove_weekly_working_hours(weekday=weekday),
            reply_markup=build_working_hours_actions_keyboard(),
        )
        await state.set_state(AdminWorkingHoursState.choosing_action)
        return

    await state.update_data(working_hours_weekday=weekday)
    await state.set_state(AdminWorkingHoursState.waiting_start_time)
    await message.answer(
        "Введите начало дня в формате ЧЧ:ММ:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminWorkingHoursState.waiting_date)
async def collect_working_hours_date(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await _send_actions_menu(message=message, state=state)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = WorkingHoursService(session=session)
    working_date = service.parse_date(message.text)

    if not working_date or working_date < date.today():
        await message.answer("Введите будущую дату в формате ДД.ММ.ГГГГ.")
        return

    data = await state.get_data()
    action = data.get("working_hours_action")

    if action == ACTION_TEMPORARY_DAY_OFF:
        await message.answer(
            await service.add_temporary_day_off(day=working_date),
            reply_markup=build_working_hours_actions_keyboard(),
        )
        await state.set_state(AdminWorkingHoursState.choosing_action)
        return

    if action == ACTION_REMOVE_TEMPORARY_WORKING_HOURS:
        await message.answer(
            await service.remove_temporary_working_hours(day=working_date),
            reply_markup=build_working_hours_actions_keyboard(),
        )
        await state.set_state(AdminWorkingHoursState.choosing_action)
        return

    await state.update_data(working_hours_date=working_date.isoformat())
    await state.set_state(AdminWorkingHoursState.waiting_start_time)
    await message.answer(
        "Введите начало дня в формате ЧЧ:ММ:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminWorkingHoursState.waiting_start_time)
async def collect_working_hours_start_time(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await _go_to_previous_selection(message=message, state=state)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = WorkingHoursService(session=session)
    start_time = service.parse_time(message.text)

    if not start_time:
        await message.answer("Введите время в формате ЧЧ:ММ.")
        return

    await state.update_data(working_hours_start_time=start_time.isoformat())
    await state.set_state(AdminWorkingHoursState.waiting_end_time)
    await message.answer(
        "Введите конец дня в формате ЧЧ:ММ:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminWorkingHoursState.waiting_end_time)
async def collect_working_hours_end_time(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AdminWorkingHoursState.waiting_start_time)
        await message.answer(
            "Введите начало дня в формате ЧЧ:ММ:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = WorkingHoursService(session=session)
    end_time = service.parse_time(message.text)

    if not end_time:
        await message.answer("Введите время в формате ЧЧ:ММ.")
        return

    await state.update_data(working_hours_end_time=end_time.isoformat())
    await state.set_state(AdminWorkingHoursState.waiting_slot_step)
    await message.answer(
        "Введите длительность сеанса/шаг в минутах:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminWorkingHoursState.waiting_slot_step)
async def collect_working_hours_slot_step(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if message.text == BACK_BUTTON:
        await state.set_state(AdminWorkingHoursState.waiting_end_time)
        await message.answer(
            "Введите конец дня в формате ЧЧ:ММ:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = WorkingHoursService(session=session)
    slot_step = service.parse_slot_step(message.text)

    if not slot_step:
        await message.answer("Введите шаг положительным числом минут.")
        return

    data = await state.get_data()
    start_time = _parse_state_time(data.get("working_hours_start_time"))
    end_time = _parse_state_time(data.get("working_hours_end_time"))

    if not start_time or not end_time:
        await state.set_state(AdminWorkingHoursState.waiting_start_time)
        await message.answer("Не хватает времени. Введите начало дня заново.")
        return

    draft = service.build_draft(
        start_time=start_time,
        end_time=end_time,
        slot_step_minutes=slot_step,
    )

    if not draft:
        await message.answer(
            "Проверьте время: начало должно быть раньше конца, шаг — внутри интервала."
        )
        return

    action = data.get("working_hours_action")

    if action == ACTION_WEEKLY_WORKING_HOURS:
        result_text = await service.set_weekly_working_hours(
            weekday=int(data["working_hours_weekday"]),
            draft=draft,
        )
    else:
        result_text = await service.set_temporary_working_hours(
            day=date.fromisoformat(data["working_hours_date"]),
            draft=draft,
        )

    await state.set_state(AdminWorkingHoursState.choosing_action)
    await message.answer(
        result_text + "\n\nЕсли этот день отмечен выходным, выходной имеет приоритет.",
        reply_markup=build_working_hours_actions_keyboard(),
    )


async def _send_actions_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminWorkingHoursState.choosing_action)
    await message.answer(
        "Рабочее время:",
        reply_markup=build_working_hours_actions_keyboard(),
    )


async def _go_to_previous_selection(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    action = data.get("working_hours_action")

    if action in {
        ACTION_WEEKLY_DAY_OFF,
        ACTION_WEEKLY_WORKING_HOURS,
        ACTION_REMOVE_WEEKLY_WORKING_HOURS,
    }:
        await state.set_state(AdminWorkingHoursState.choosing_weekday)
        await message.answer(
            "Выберите день недели:", reply_markup=build_weekday_keyboard()
        )
        return

    await state.set_state(AdminWorkingHoursState.waiting_date)
    await message.answer(
        "Введите дату в формате ДД.ММ.ГГГГ:",
        reply_markup=build_back_main_keyboard(),
    )


async def _handle_common_navigation(message: Message, state: FSMContext) -> bool:
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return True

    return False


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)


def _parse_state_time(value: str | None) -> time | None:
    if not value:
        return None

    try:
        return time.fromisoformat(value)
    except ValueError:
        return None
