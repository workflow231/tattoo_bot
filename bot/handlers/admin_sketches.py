from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    ADD_SKETCH_BUTTON,
    ADMIN_SKETCHES_BUTTON,
    BACK_BUTTON,
    CATALOG_PAGE_SIZE,
    CONFIRM_CREATE_SKETCH_BUTTON,
    CONFIRM_DELETE_SKETCH_BUTTON,
    CONFIRM_DELETE_STYLE_BUTTON,
    CREATE_STYLE_BUTTON,
    DELETE_SKETCH_BUTTON,
    DELETE_STYLE_BUTTON,
    EDIT_SKETCH_DESCRIPTION_BUTTON,
    EDIT_SKETCH_BUTTON,
    EDIT_SKETCH_NAME_BUTTON,
    EDIT_SKETCH_PHOTO_BUTTON,
    EDIT_SKETCH_PRICE_BUTTON,
    EDIT_SKETCH_STATUS_BUTTON,
    EDIT_SKETCH_STYLE_BUTTON,
    EDIT_STYLE_BUTTON,
    MAIN_MENU_BUTTON,
    NEXT_PAGE_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    SKIP_COMMENT_BUTTON,
    build_admin_sketch_actions_keyboard,
    build_admin_sketch_confirm_keyboard,
    build_admin_sketch_edit_fields_keyboard,
    build_admin_sketch_select_keyboard,
    build_admin_sketch_style_names_keyboard,
    build_admin_sketch_status_keyboard,
    build_admin_sketch_style_keyboard,
    build_admin_style_select_keyboard,
    build_admin_delete_confirm_keyboard,
    build_back_main_keyboard,
    build_skip_back_main_keyboard,
    format_admin_sketch_button_text,
    master_menu_kb,
)
from bot.states import AdminSketchState
from services.admin_appointment_service import AdminAppointmentService
from services.admin_sketch_service import AdminSketchService, SketchDraft
from utils.config import is_simple_bot

router = Router()

ACTION_DELETE_STYLE = "delete_style"
ACTION_EDIT_STYLE = "edit_style"
ACTION_DELETE_SKETCH = "delete_sketch"
ACTION_EDIT_SKETCH = "edit_sketch"

EDIT_FIELD_BY_BUTTON = {
    EDIT_SKETCH_NAME_BUTTON: "name",
    EDIT_SKETCH_DESCRIPTION_BUTTON: "description",
    EDIT_SKETCH_PRICE_BUTTON: "price",
    EDIT_SKETCH_PHOTO_BUTTON: "photo",
    EDIT_SKETCH_STATUS_BUTTON: "status",
    EDIT_SKETCH_STYLE_BUTTON: "style",
}


@router.message(F.text == ADMIN_SKETCHES_BUTTON)
async def show_admin_sketch_actions(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.")
        return

    await _send_sketch_actions_menu(message=message, state=state)


@router.message(AdminSketchState.choosing_action)
async def choose_admin_sketch_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if message.text == BACK_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    simple_bot = is_simple_bot()

    if message.text == ADD_SKETCH_BUTTON:
        await _start_add_sketch_flow(
            session=session,
            message=message,
            state=state,
            simple_bot=simple_bot,
        )
        return

    if message.text == DELETE_STYLE_BUTTON and not simple_bot:
        await _send_style_management_selection(
            session=session,
            message=message,
            state=state,
            action=ACTION_DELETE_STYLE,
            target_state=AdminSketchState.choosing_style_to_delete,
        )
        return

    if message.text == EDIT_STYLE_BUTTON and not simple_bot:
        await _send_style_management_selection(
            session=session,
            message=message,
            state=state,
            action=ACTION_EDIT_STYLE,
            target_state=AdminSketchState.choosing_style_to_edit,
        )
        return

    if message.text == DELETE_SKETCH_BUTTON:
        await _send_sketch_management_selection(
            session=session,
            message=message,
            state=state,
            action=ACTION_DELETE_SKETCH,
            target_state=AdminSketchState.choosing_sketch_to_delete,
        )
        return

    if message.text == EDIT_SKETCH_BUTTON:
        await _send_sketch_management_selection(
            session=session,
            message=message,
            state=state,
            action=ACTION_EDIT_SKETCH,
            target_state=AdminSketchState.choosing_sketch_to_edit,
        )
        return

    await message.answer(
        "Выберите действие кнопкой.",
        reply_markup=build_admin_sketch_actions_keyboard(),
    )


@router.message(AdminSketchState.choosing_style_to_delete)
async def choose_style_to_delete(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await _handle_style_management_selection(
        message=message,
        state=state,
        session=session,
        action=ACTION_DELETE_STYLE,
        target_state=AdminSketchState.choosing_style_to_delete,
    )


@router.message(AdminSketchState.confirming_style_delete)
async def confirm_style_delete(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if message.text != CONFIRM_DELETE_STYLE_BUTTON:
        await message.answer(
            "Подтвердите удаление кнопкой или вернитесь назад.",
            reply_markup=build_admin_delete_confirm_keyboard(
                CONFIRM_DELETE_STYLE_BUTTON
            ),
        )
        return

    data = await state.get_data()
    style_id = data.get("selected_admin_style_id")

    if not style_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await AdminSketchService(session=session).delete_style(
        style_id=int(style_id),
    )
    await _send_sketch_actions_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.choosing_style_to_edit)
async def choose_style_to_edit(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await _handle_style_management_selection(
        message=message,
        state=state,
        session=session,
        action=ACTION_EDIT_STYLE,
        target_state=AdminSketchState.choosing_style_to_edit,
    )


@router.message(AdminSketchState.waiting_style_name)
async def collect_new_style_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _send_sketch_actions_menu(message=message, state=state)
        return

    data = await state.get_data()
    style_id = data.get("selected_admin_style_id")

    if not style_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await AdminSketchService(session=session).rename_style(
        style_id=int(style_id),
        style_name=message.text or "",
    )
    await _send_sketch_actions_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.choosing_sketch_to_delete)
async def choose_sketch_to_delete(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await _handle_sketch_management_selection(
        message=message,
        state=state,
        session=session,
        action=ACTION_DELETE_SKETCH,
        target_state=AdminSketchState.choosing_sketch_to_delete,
    )


@router.message(AdminSketchState.confirming_sketch_delete)
async def confirm_sketch_delete(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if message.text != CONFIRM_DELETE_SKETCH_BUTTON:
        await message.answer(
            "Подтвердите удаление кнопкой или вернитесь назад.",
            reply_markup=build_admin_delete_confirm_keyboard(
                CONFIRM_DELETE_SKETCH_BUTTON
            ),
        )
        return

    data = await state.get_data()
    sketch_id = data.get("selected_admin_sketch_id")

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await AdminSketchService(session=session).delete_sketch(
        sketch_id=int(sketch_id),
    )
    await _send_sketch_actions_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.choosing_sketch_to_edit)
async def choose_sketch_to_edit(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await _handle_sketch_management_selection(
        message=message,
        state=state,
        session=session,
        action=ACTION_EDIT_SKETCH,
        target_state=AdminSketchState.choosing_sketch_to_edit,
    )


@router.message(AdminSketchState.choosing_sketch_field)
async def choose_sketch_field_to_edit(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    field = EDIT_FIELD_BY_BUTTON.get(message.text or "")

    if not field or (field == "style" and is_simple_bot()):
        await message.answer(
            "Выберите поле кнопкой.",
            reply_markup=build_admin_sketch_edit_fields_keyboard(),
        )
        return

    await state.update_data(admin_sketch_edit_field=field)

    if field == "name":
        await state.set_state(AdminSketchState.waiting_edit_sketch_name)
        await message.answer(
            "Введите новое название:", reply_markup=build_back_main_keyboard()
        )
        return

    if field == "description":
        await state.set_state(AdminSketchState.waiting_edit_sketch_description)
        await message.answer(
            "Введите новое описание или нажмите «Пропустить»:",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if field == "price":
        await state.set_state(AdminSketchState.waiting_edit_sketch_price)
        await message.answer(
            "Введите новую цену числом или нажмите «Пропустить»:",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if field == "photo":
        await state.set_state(AdminSketchState.waiting_edit_sketch_photo)
        await message.answer(
            "Отправьте новое фото, file_id текстом или нажмите «Пропустить»:",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if field == "status":
        await state.set_state(AdminSketchState.waiting_edit_sketch_status)
        await message.answer(
            "Выберите новый статус:",
            reply_markup=build_admin_sketch_status_keyboard(),
        )
        return

    await _send_style_management_selection(
        session=session,
        message=message,
        state=state,
        action=ACTION_EDIT_SKETCH,
        target_state=AdminSketchState.choosing_sketch_style,
    )


@router.message(AdminSketchState.waiting_edit_sketch_name)
async def collect_edit_sketch_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await AdminSketchService(session=session).update_sketch_name(
        sketch_id=sketch_id,
        name=message.text or "",
    )
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.waiting_edit_sketch_description)
async def collect_edit_sketch_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    service = AdminSketchService(session=session)
    result_text = await service.update_sketch_description(
        sketch_id=sketch_id,
        description=service.parse_optional_text(message.text),
    )
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.waiting_edit_sketch_price)
async def collect_edit_sketch_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    price = service.parse_optional_price(message.text)

    if price is None and (message.text or "").strip() != SKIP_COMMENT_BUTTON:
        await message.answer("Введите цену числом или нажмите «Пропустить».")
        return

    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await service.update_sketch_price(sketch_id=sketch_id, price=price)
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.waiting_edit_sketch_photo)
async def collect_edit_sketch_photo(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    photo_file_id = (
        message.photo[-1].file_id
        if message.photo
        else service.parse_optional_text(message.text)
    )
    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await service.update_sketch_photo(
        sketch_id=sketch_id,
        photo_file_id=photo_file_id,
    )
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.waiting_edit_sketch_status)
async def collect_edit_sketch_status(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    status = service.parse_status(message.text)

    if not status:
        await message.answer(
            "Выберите статус кнопкой.",
            reply_markup=build_admin_sketch_status_keyboard(),
        )
        return

    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await service.update_sketch_status(
        sketch_id=sketch_id,
        status=status,
    )
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


@router.message(AdminSketchState.choosing_sketch_style)
async def choose_edit_sketch_style(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _send_sketch_actions_menu(message=message, state=state)
        return

    data = await state.get_data()

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_style_management_selection(
            session=session,
            message=message,
            state=state,
            action=ACTION_EDIT_SKETCH,
            target_state=AdminSketchState.choosing_sketch_style,
            page=_shift_page(
                current_page=int(data.get("admin_style_page", 0)),
                step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
                items_count=len(data.get("admin_style_buttons", {})),
            ),
        )
        return

    style_buttons: dict[str, int] = data.get("admin_style_buttons", {})
    style_id = style_buttons.get(message.text or "")

    if not style_id:
        await message.answer("Выберите категорию кнопкой из списка.")
        return

    sketch_id = await _get_selected_sketch_id(state=state)

    if not sketch_id:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    result_text = await AdminSketchService(session=session).update_sketch_style(
        sketch_id=sketch_id,
        style_id=style_id,
    )
    await _send_sketch_edit_menu(message=message, state=state, prefix=result_text)


async def _handle_style_management_selection(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    action: str,
    target_state,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _send_sketch_actions_menu(message=message, state=state)
        return

    data = await state.get_data()

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_style_management_selection(
            session=session,
            message=message,
            state=state,
            action=action,
            target_state=target_state,
            page=_shift_page(
                current_page=int(data.get("admin_style_page", 0)),
                step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
                items_count=len(data.get("admin_style_buttons", {})),
            ),
        )
        return

    style_buttons: dict[str, int] = data.get("admin_style_buttons", {})
    style_id = style_buttons.get(message.text or "")

    if not style_id:
        await message.answer("Выберите категорию кнопкой из списка.")
        return

    await state.update_data(
        selected_admin_style_id=style_id,
        selected_admin_style_name=message.text,
    )

    if action == ACTION_DELETE_STYLE:
        await state.set_state(AdminSketchState.confirming_style_delete)
        await message.answer(
            AdminSketchService(session=session).build_style_delete_confirmation_text(
                message.text or ""
            ),
            reply_markup=build_admin_delete_confirm_keyboard(
                CONFIRM_DELETE_STYLE_BUTTON
            ),
        )
        return

    await state.set_state(AdminSketchState.waiting_style_name)
    await message.answer(
        "Введите новое название категории:",
        reply_markup=build_back_main_keyboard(),
    )


async def _handle_sketch_management_selection(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    action: str,
    target_state,
) -> None:
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    data = await state.get_data()

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_sketch_management_selection(
            session=session,
            message=message,
            state=state,
            action=action,
            target_state=target_state,
            page=_shift_page(
                current_page=int(data.get("admin_sketch_page", 0)),
                step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
                items_count=len(data.get("admin_sketch_buttons", {})),
            ),
        )
        return

    sketch_buttons: dict[str, int] = data.get("admin_sketch_buttons", {})
    sketch_id = sketch_buttons.get(message.text or "")

    if not sketch_id:
        await message.answer("Выберите услугу кнопкой из списка.")
        return

    service = AdminSketchService(session=session)
    sketch = await service.get_sketch(sketch_id=sketch_id)

    if not sketch:
        await message.answer("Услуга не найдена.")
        return

    await state.update_data(selected_admin_sketch_id=sketch.id)

    if action == ACTION_DELETE_SKETCH:
        await state.set_state(AdminSketchState.confirming_sketch_delete)
        await message.answer(
            service.build_sketch_delete_confirmation_text(sketch),
            reply_markup=build_admin_delete_confirm_keyboard(
                CONFIRM_DELETE_SKETCH_BUTTON
            ),
        )
        return

    await _send_sketch_edit_menu(
        message=message,
        state=state,
        prefix=service.build_sketch_card_text(sketch),
    )


@router.message(F.text == ADD_SKETCH_BUTTON)
async def start_add_sketch(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    if not _message_from_admin(session=session, message=message):
        await message.answer("Недостаточно прав.")
        return

    await _start_add_sketch_flow(
        session=session,
        message=message,
        state=state,
        simple_bot=is_simple_bot(),
    )


async def _start_add_sketch_flow(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    simple_bot: bool,
) -> None:
    if simple_bot:
        service = AdminSketchService(session=session)
        style = await service.get_or_create_default_style()
        await state.update_data(
            admin_sketch_style_id=style.id,
            admin_sketch_style_name=style.name,
        )
        await state.set_state(AdminSketchState.waiting_name)
        await message.answer(
            "Введите название услуги:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    await _send_style_choice(session=session, message=message, state=state)


@router.message(AdminSketchState.choosing_style)
async def choose_sketch_style(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _start_add_sketch_flow(
            session=session,
            message=message,
            state=state,
            simple_bot=True,
        )
        return

    if message.text == CREATE_STYLE_BUTTON:
        await state.set_state(AdminSketchState.waiting_new_style_name)
        await message.answer(
            "Введите название новой категории:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("admin_sketch_style_buttons", {})
    style_id = style_buttons.get(message.text or "")

    if not style_id:
        await message.answer("Выберите категорию кнопкой из списка.")
        return

    await state.update_data(
        admin_sketch_style_id=style_id,
        admin_sketch_style_name=message.text,
    )
    await state.set_state(AdminSketchState.waiting_name)
    await message.answer(
        "Введите название услуги:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_new_style_name)
async def create_new_style(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if is_simple_bot():
        await _send_sketch_actions_menu(message=message, state=state)
        return

    style_name = (message.text or "").strip()

    if not style_name or style_name == SKIP_COMMENT_BUTTON:
        await message.answer("Введите название новой категории текстом.")
        return

    service = AdminSketchService(session=session)
    style = await service.create_style(style_name=style_name)
    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("admin_sketch_style_buttons", {})
    style_buttons[style.name] = style.id

    await state.update_data(
        admin_sketch_style_id=style.id,
        admin_sketch_style_name=style.name,
        admin_sketch_style_buttons=style_buttons,
    )
    await state.set_state(AdminSketchState.waiting_name)
    await message.answer(
        "Категория выбрана. Введите название услуги:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_name)
async def collect_sketch_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    name = (message.text or "").strip()

    if not name or name == SKIP_COMMENT_BUTTON:
        await message.answer("Название обязательно. Введите название услуги.")
        return

    await state.update_data(admin_sketch_name=name)
    await state.set_state(AdminSketchState.waiting_description)
    await message.answer(
        "Введите описание услуги или нажмите «Пропустить»:",
        reply_markup=build_skip_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_description)
async def collect_sketch_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    await state.update_data(
        admin_sketch_description=service.parse_optional_text(message.text)
    )
    await state.set_state(AdminSketchState.waiting_price)
    await message.answer(
        "Введите цену числом или нажмите «Пропустить» для договорной цены:",
        reply_markup=build_skip_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_price)
async def collect_sketch_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    price = service.parse_optional_price(message.text)

    if price is None and (message.text or "").strip() != SKIP_COMMENT_BUTTON:
        await message.answer("Введите цену числом или нажмите «Пропустить».")
        return

    await state.update_data(admin_sketch_price=price)
    await state.set_state(AdminSketchState.waiting_photo)
    await message.answer(
        "Отправьте фото услуги или file_id текстом. Можно нажать «Пропустить».",
        reply_markup=build_skip_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_photo)
async def collect_sketch_photo(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    photo_file_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        photo_file_id = service.parse_optional_text(message.text)

    await state.update_data(admin_sketch_photo_file_id=photo_file_id)
    await state.set_state(AdminSketchState.waiting_status)
    await message.answer(
        "Выберите статус услуги:",
        reply_markup=build_admin_sketch_status_keyboard(),
    )


@router.message(AdminSketchState.waiting_status)
async def collect_sketch_status(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    service = AdminSketchService(session=session)
    status = service.parse_status(message.text)

    if not status:
        await message.answer(
            "Выберите статус кнопкой.",
            reply_markup=build_admin_sketch_status_keyboard(),
        )
        return

    await state.update_data(admin_sketch_status=status)

    data = await state.get_data()
    if status == "available" and not data.get("admin_sketch_photo_file_id"):
        await state.set_state(AdminSketchState.waiting_photo)
        await message.answer(
            "Для доступной услуги нужно фото. Отправьте фото или file_id.",
            reply_markup=build_back_main_keyboard(),
        )
        return

    draft = _build_draft_from_state(await state.get_data())

    if not draft:
        await state.clear()
        await message.answer(
            "Не хватает данных для услуги.", reply_markup=master_menu_kb
        )
        return

    await state.set_state(AdminSketchState.confirming)
    await message.answer(
        service.build_summary_text(draft)
        + "\n\nНажмите «Сохранить услугу» для сохранения.",
        reply_markup=build_admin_sketch_confirm_keyboard(),
    )


@router.message(AdminSketchState.confirming)
async def confirm_sketch_creation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    if not _message_from_admin(session=session, message=message):
        await state.clear()
        await message.answer("Недостаточно прав.")
        return

    if message.text != CONFIRM_CREATE_SKETCH_BUTTON:
        await message.answer(
            "Подтвердите сохранение кнопкой «Сохранить услугу» или вернитесь назад.",
            reply_markup=build_admin_sketch_confirm_keyboard(),
        )
        return

    draft = _build_draft_from_state(await state.get_data())

    if not draft:
        await state.clear()
        await message.answer(
            "Не хватает данных для услуги.", reply_markup=master_menu_kb
        )
        return

    service = AdminSketchService(session=session)
    sketch = await service.create_sketch(draft=draft)
    await state.clear()
    await message.answer(
        f"Услуга #{sketch.id} добавлена.",
        reply_markup=master_menu_kb,
    )


async def _send_style_choice(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
) -> None:
    service = AdminSketchService(session=session)
    styles = await service.get_styles()
    style_buttons = {style.name: style.id for style in styles}

    await state.update_data(admin_sketch_style_buttons=style_buttons)
    await state.set_state(AdminSketchState.choosing_style)
    await message.answer(
        "Выберите категорию для услуги:",
        reply_markup=build_admin_sketch_style_keyboard(styles),
    )


async def _send_style_management_selection(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    action: str,
    target_state,
    page: int = 0,
) -> None:
    service = AdminSketchService(session=session)
    styles = await service.get_styles()

    if not styles:
        await _send_sketch_actions_menu(
            message=message,
            state=state,
            prefix="Категории пока не добавлены.",
        )
        return

    await state.update_data(
        admin_sketch_action=action,
        admin_style_buttons={style.name: style.id for style in styles},
        admin_style_page=page,
    )
    await state.set_state(target_state)
    await message.answer(
        _build_selection_text(
            title="Выберите категорию",
            page=page,
            items_count=len(styles),
        ),
        reply_markup=build_admin_style_select_keyboard(styles=styles, page=page),
    )


async def _send_sketch_management_selection(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    action: str,
    target_state,
    page: int = 0,
) -> None:
    service = AdminSketchService(session=session)
    sketches = await service.get_sketches()

    if not sketches:
        await _send_sketch_actions_menu(
            message=message,
            state=state,
            prefix="Услуги пока не добавлены.",
        )
        return

    await state.update_data(
        admin_sketch_action=action,
        admin_sketch_buttons={
            format_admin_sketch_button_text(sketch): sketch.id for sketch in sketches
        },
        admin_sketch_page=page,
    )
    await state.set_state(target_state)
    await message.answer(
        _build_selection_text(
            title="Выберите услугу",
            page=page,
            items_count=len(sketches),
        ),
        reply_markup=build_admin_sketch_select_keyboard(sketches=sketches, page=page),
    )


async def _send_sketch_edit_menu(
    message: Message,
    state: FSMContext,
    prefix: str | None = None,
) -> None:
    await state.set_state(AdminSketchState.choosing_sketch_field)
    text = "Выберите поле для изменения:"

    if prefix:
        text = f"{prefix}\n\n{text}"

    await message.answer(
        text,
        reply_markup=build_admin_sketch_edit_fields_keyboard(),
    )


async def _send_sketch_actions_menu(
    message: Message,
    state: FSMContext,
    prefix: str | None = None,
) -> None:
    await state.set_state(AdminSketchState.choosing_action)
    text = "Выберите действие с услугами:"

    if prefix:
        text = f"{prefix}\n\n{text}"

    await message.answer(
        text,
        reply_markup=build_admin_sketch_actions_keyboard(),
    )


async def _handle_common_navigation(message: Message, state: FSMContext) -> bool:
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return True

    if message.text == BACK_BUTTON:
        await _handle_back_navigation(message=message, state=state)
        return True

    return False


async def _handle_back_navigation(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AdminSketchState.choosing_action.state:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if current_state in {
        AdminSketchState.choosing_style_to_delete.state,
        AdminSketchState.choosing_style_to_edit.state,
        AdminSketchState.choosing_sketch_to_delete.state,
        AdminSketchState.choosing_sketch_to_edit.state,
    }:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.confirming_style_delete.state:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.waiting_style_name.state:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.confirming_sketch_delete.state:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.choosing_sketch_field.state:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state in {
        AdminSketchState.waiting_edit_sketch_name.state,
        AdminSketchState.waiting_edit_sketch_description.state,
        AdminSketchState.waiting_edit_sketch_price.state,
        AdminSketchState.waiting_edit_sketch_photo.state,
        AdminSketchState.waiting_edit_sketch_status.state,
        AdminSketchState.choosing_sketch_style.state,
    }:
        await _send_sketch_edit_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.choosing_style.state:
        await _send_sketch_actions_menu(message=message, state=state)
        return

    if current_state == AdminSketchState.waiting_new_style_name.state:
        if is_simple_bot():
            await _send_sketch_actions_menu(message=message, state=state)
            return

        await state.set_state(AdminSketchState.choosing_style)
        await message.answer(
            "Выберите категорию для услуги:",
            reply_markup=build_admin_sketch_style_names_keyboard(
                await _get_style_names_from_state(state=state)
            ),
        )
        return

    if current_state == AdminSketchState.waiting_name.state:
        if is_simple_bot():
            await _send_sketch_actions_menu(message=message, state=state)
            return

        await state.set_state(AdminSketchState.choosing_style)
        await message.answer(
            "Выберите категорию для услуги:",
            reply_markup=build_admin_sketch_style_names_keyboard(
                await _get_style_names_from_state(state=state)
            ),
        )
        return

    if current_state == AdminSketchState.waiting_description.state:
        await state.set_state(AdminSketchState.waiting_name)
        await message.answer(
            "Введите название услуги:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.waiting_price.state:
        await state.set_state(AdminSketchState.waiting_description)
        await message.answer(
            "Введите описание услуги или нажмите «Пропустить»:",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.waiting_photo.state:
        await state.set_state(AdminSketchState.waiting_price)
        await message.answer(
            "Введите цену числом или нажмите «Пропустить» для договорной цены:",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.waiting_status.state:
        await state.set_state(AdminSketchState.waiting_photo)
        await message.answer(
            "Отправьте фото услуги или file_id текстом. Можно нажать «Пропустить».",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.confirming.state:
        await state.set_state(AdminSketchState.waiting_status)
        await message.answer(
            "Выберите статус услуги:",
            reply_markup=build_admin_sketch_status_keyboard(),
        )
        return

    await state.clear()
    await message.answer("Главное меню", reply_markup=master_menu_kb)


async def _get_style_names_from_state(state: FSMContext) -> list[str]:
    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("admin_sketch_style_buttons", {})
    return list(style_buttons)


def _build_draft_from_state(data: dict) -> SketchDraft | None:
    required_keys = (
        "admin_sketch_style_id",
        "admin_sketch_style_name",
        "admin_sketch_name",
        "admin_sketch_status",
    )

    if any(key not in data for key in required_keys):
        return None

    return SketchDraft(
        style_id=int(data["admin_sketch_style_id"]),
        style_name=str(data["admin_sketch_style_name"]),
        name=str(data["admin_sketch_name"]),
        description=data.get("admin_sketch_description"),
        price=data.get("admin_sketch_price"),
        photo_file_id=data.get("admin_sketch_photo_file_id"),
        status=str(data["admin_sketch_status"]),
    )


async def _get_selected_sketch_id(state: FSMContext) -> int | None:
    data = await state.get_data()
    sketch_id = data.get("selected_admin_sketch_id")

    if not sketch_id:
        return None

    return int(sketch_id)


def _shift_page(current_page: int, step: int, items_count: int) -> int:
    if items_count <= CATALOG_PAGE_SIZE:
        return 0

    max_page = (items_count - 1) // CATALOG_PAGE_SIZE
    next_page = current_page + step

    if next_page < 0:
        return 0

    if next_page > max_page:
        return max_page

    return next_page


def _build_selection_text(title: str, page: int, items_count: int) -> str:
    if items_count <= CATALOG_PAGE_SIZE:
        return f"{title}:"

    total_pages = (items_count - 1) // CATALOG_PAGE_SIZE + 1
    return f"{title} ({page + 1}/{total_pages}):"


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)
