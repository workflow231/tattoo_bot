from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    ADD_SKETCH_BUTTON,
    BACK_BUTTON,
    CONFIRM_CREATE_SKETCH_BUTTON,
    CREATE_STYLE_BUTTON,
    MAIN_MENU_BUTTON,
    SKIP_COMMENT_BUTTON,
    build_admin_sketch_confirm_keyboard,
    build_admin_sketch_style_names_keyboard,
    build_admin_sketch_status_keyboard,
    build_admin_sketch_style_keyboard,
    build_back_main_keyboard,
    build_skip_back_main_keyboard,
    master_menu_kb,
)
from bot.states import AdminSketchState
from services.admin_appointment_service import AdminAppointmentService
from services.admin_sketch_service import AdminSketchService, SketchDraft

router = Router()


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

    if message.text == CREATE_STYLE_BUTTON:
        await state.set_state(AdminSketchState.waiting_new_style_name)
        await message.answer(
            "Введите название нового стиля:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("admin_sketch_style_buttons", {})
    style_id = style_buttons.get(message.text or "")

    if not style_id:
        await message.answer("Выберите стиль кнопкой из списка.")
        return

    await state.update_data(
        admin_sketch_style_id=style_id,
        admin_sketch_style_name=message.text,
    )
    await state.set_state(AdminSketchState.waiting_name)
    await message.answer(
        "Введите название эскиза:",
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

    style_name = (message.text or "").strip()

    if not style_name or style_name == SKIP_COMMENT_BUTTON:
        await message.answer("Введите название нового стиля текстом.")
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
        "Стиль выбран. Введите название эскиза:",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_name)
async def collect_sketch_name(message: Message, state: FSMContext):
    if await _handle_common_navigation(message=message, state=state):
        return

    name = (message.text or "").strip()

    if not name or name == SKIP_COMMENT_BUTTON:
        await message.answer("Название обязательно. Введите название эскиза.")
        return

    await state.update_data(admin_sketch_name=name)
    await state.set_state(AdminSketchState.waiting_description)
    await message.answer(
        "Введите описание эскиза или нажмите «Пропустить»:",
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

    service = AdminSketchService(session=session)
    price = service.parse_optional_price(message.text)

    if price is None and (message.text or "").strip() != SKIP_COMMENT_BUTTON:
        await message.answer("Введите цену числом или нажмите «Пропустить».")
        return

    await state.update_data(admin_sketch_price=price)
    await state.set_state(AdminSketchState.waiting_photo)
    await message.answer(
        "Отправьте фото эскиза или file_id текстом. Можно нажать «Пропустить».",
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

    service = AdminSketchService(session=session)
    photo_file_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        photo_file_id = service.parse_optional_text(message.text)

    await state.update_data(admin_sketch_photo_file_id=photo_file_id)
    await state.set_state(AdminSketchState.waiting_status)
    await message.answer(
        "Выберите статус эскиза:",
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
            "Для доступного эскиза нужно фото. Отправьте фото или file_id.",
            reply_markup=build_back_main_keyboard(),
        )
        return

    await state.set_state(AdminSketchState.waiting_views)
    await message.answer(
        "Введите количество просмотров числом. Для нового эскиза обычно 0.",
        reply_markup=build_back_main_keyboard(),
    )


@router.message(AdminSketchState.waiting_views)
async def collect_sketch_views(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if await _handle_common_navigation(message=message, state=state):
        return

    service = AdminSketchService(session=session)
    views = service.parse_views(message.text)

    if views is None:
        await message.answer("Введите количество просмотров числом.")
        return

    await state.update_data(admin_sketch_views=views)
    draft = _build_draft_from_state(await state.get_data())

    if not draft:
        await state.clear()
        await message.answer(
            "Не хватает данных для эскиза.", reply_markup=master_menu_kb
        )
        return

    await state.set_state(AdminSketchState.confirming)
    await message.answer(
        service.build_summary_text(draft)
        + "\n\nНажмите «Сохранить эскиз» для сохранения.",
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

    if message.text != CONFIRM_CREATE_SKETCH_BUTTON:
        await message.answer(
            "Подтвердите сохранение кнопкой «Сохранить эскиз» или вернитесь назад.",
            reply_markup=build_admin_sketch_confirm_keyboard(),
        )
        return

    draft = _build_draft_from_state(await state.get_data())

    if not draft:
        await state.clear()
        await message.answer(
            "Не хватает данных для эскиза.", reply_markup=master_menu_kb
        )
        return

    service = AdminSketchService(session=session)
    sketch = await service.create_sketch(draft=draft)
    await state.clear()
    await message.answer(
        f"Эскиз #{sketch.id} добавлен.",
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
        "Выберите стиль для эскиза:",
        reply_markup=build_admin_sketch_style_keyboard(styles),
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

    if current_state == AdminSketchState.choosing_style.state:
        await state.clear()
        await message.answer("Главное меню", reply_markup=master_menu_kb)
        return

    if current_state == AdminSketchState.waiting_new_style_name.state:
        await state.set_state(AdminSketchState.choosing_style)
        await message.answer(
            "Выберите стиль для эскиза:",
            reply_markup=build_admin_sketch_style_names_keyboard(
                await _get_style_names_from_state(state=state)
            ),
        )
        return

    if current_state == AdminSketchState.waiting_name.state:
        await state.set_state(AdminSketchState.choosing_style)
        await message.answer(
            "Выберите стиль для эскиза:",
            reply_markup=build_admin_sketch_style_names_keyboard(
                await _get_style_names_from_state(state=state)
            ),
        )
        return

    if current_state == AdminSketchState.waiting_description.state:
        await state.set_state(AdminSketchState.waiting_name)
        await message.answer(
            "Введите название эскиза:",
            reply_markup=build_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.waiting_price.state:
        await state.set_state(AdminSketchState.waiting_description)
        await message.answer(
            "Введите описание эскиза или нажмите «Пропустить»:",
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
            "Отправьте фото эскиза или file_id текстом. Можно нажать «Пропустить».",
            reply_markup=build_skip_back_main_keyboard(),
        )
        return

    if current_state == AdminSketchState.waiting_views.state:
        await state.set_state(AdminSketchState.waiting_status)
        await message.answer(
            "Выберите статус эскиза:",
            reply_markup=build_admin_sketch_status_keyboard(),
        )
        return

    if current_state == AdminSketchState.confirming.state:
        await state.set_state(AdminSketchState.waiting_views)
        await message.answer(
            "Введите количество просмотров числом. Для нового эскиза обычно 0.",
            reply_markup=build_back_main_keyboard(),
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
        "admin_sketch_views",
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
        views=int(data["admin_sketch_views"]),
    )


def _message_from_admin(session: AsyncSession, message: Message) -> bool:
    if not message.from_user:
        return False

    service = AdminAppointmentService(session=session)
    return service.is_admin(telegram_id=message.from_user.id)
