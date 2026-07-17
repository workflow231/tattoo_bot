from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CATALOG_PAGE_SIZE,
    CHAT_WITH_MASTER_BUTTON,
    MAIN_MENU_BUTTON,
    NEXT_PAGE_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    build_sketches_reply_keyboard,
    build_styles_reply_keyboard,
    sketch_card_kb,
)
from bot.menu_utils import get_main_menu_for_message
from services.sketch_catalog_service import SketchCatalogService
from services.master_contact_service import MasterContactService
from bot.states import SketchCatalogState

router = Router()


@router.message(F.text == "Каталог эскизов")
async def sketch_catalog(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()

    service = SketchCatalogService(session=session)

    styles = await service.get_styles()

    if not styles:
        await message.answer(
            "К сожалению, список стилей пока пуст, но он обязательно скоро появится.",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    style_buttons = _build_style_buttons(styles=styles, page=0)

    await state.update_data(style_buttons=style_buttons, style_page=0)
    await state.set_state(SketchCatalogState.choosing_style)

    await service.send_styles_catalog(
        message=message,
        styles=styles,
    )


@router.message(SketchCatalogState.choosing_style)
async def choose_style(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer(
            "Главное меню",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("style_buttons", {})

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_styles_page(
            session=session,
            message=message,
            state=state,
            current_page=int(data.get("style_page", 0)),
            step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
        )
        return

    style_id = style_buttons.get(message.text)

    if not style_id:
        await message.answer("Выберите стиль кнопкой из списка.")
        return

    service = SketchCatalogService(session=session)

    sketches = await service.get_sketches_by_style_id(style_id=style_id)

    if not sketches:
        await message.answer("В этом стиле пока нет доступных эскизов.")
        return

    sketch_buttons = _build_sketch_buttons(sketches=sketches, page=0)

    await state.update_data(
        style_id=style_id,
        sketch_buttons=sketch_buttons,
        sketch_page=0,
    )
    await state.set_state(SketchCatalogState.choosing_sketch)

    await service.send_sketches_catalog(
        message=message,
        sketches=sketches,
    )


@router.message(SketchCatalogState.choosing_sketch)
async def choose_sketch(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer(
            "Главное меню",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == BACK_BUTTON:
        await state.clear()

        service = SketchCatalogService(session=session)

        styles = await service.get_styles()

        if not styles:
            await message.answer(
                "К сожалению, список стилей пока пуст.",
                reply_markup=get_main_menu_for_message(
                    session=session,
                    message=message,
                ),
            )
            return

        style_buttons = _build_style_buttons(styles=styles, page=0)

        await state.update_data(style_buttons=style_buttons, style_page=0)
        await state.set_state(SketchCatalogState.choosing_style)

        await service.send_styles_catalog(
            message=message,
            styles=styles,
        )
        return

    data = await state.get_data()
    sketch_buttons: dict[str, int] = data.get("sketch_buttons", {})

    if message.text in {PREVIOUS_PAGE_BUTTON, NEXT_PAGE_BUTTON}:
        await _send_sketches_page(
            session=session,
            message=message,
            state=state,
            current_page=int(data.get("sketch_page", 0)),
            step=-1 if message.text == PREVIOUS_PAGE_BUTTON else 1,
        )
        return

    sketch_id = sketch_buttons.get(message.text)

    if not sketch_id:
        await message.answer("Выберите эскиз кнопкой из списка.")
        return

    service = SketchCatalogService(session=session)

    sketch = await service.get_sketch_by_id(sketch_id=sketch_id)

    if not sketch:
        await message.answer("Эскиз не найден или уже недоступен.")
        return

    await state.update_data(sketch_id=sketch.id)
    await state.set_state(SketchCatalogState.sketch_selected)

    await service.send_selected_sketch_card(
        message=message,
        sketch=sketch,
    )


@router.message(SketchCatalogState.sketch_selected)
async def sketch_selected_actions(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer(
            "Главное меню",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == BACK_BUTTON:
        data = await state.get_data()
        style_id = data.get("style_id")

        if not style_id:
            await state.clear()
            await message.answer(
                "Не удалось вернуться к списку эскизов. Откройте каталог заново.",
                reply_markup=get_main_menu_for_message(
                    session=session,
                    message=message,
                ),
            )
            return

        service = SketchCatalogService(session=session)
        sketches = await service.get_sketches_by_style_id(style_id=style_id)

        if not sketches:
            await state.clear()
            await message.answer(
                "В этом стиле пока нет доступных эскизов.",
                reply_markup=get_main_menu_for_message(
                    session=session,
                    message=message,
                ),
            )
            return

        sketch_page = int(data.get("sketch_page", 0))
        sketch_buttons = _build_sketch_buttons(sketches=sketches, page=sketch_page)

        await state.update_data(sketch_buttons=sketch_buttons)
        await state.set_state(SketchCatalogState.choosing_sketch)
        await service.send_sketches_catalog(
            message=message,
            sketches=sketches,
        )
        return

    if message.text == CHAT_WITH_MASTER_BUTTON:
        await message.answer(
            MasterContactService().get_contact_text(),
            reply_markup=sketch_card_kb,
        )
        return

    await message.answer(
        "Выберите действие кнопкой.",
        reply_markup=sketch_card_kb,
    )


def _build_sketch_button_text(sketch) -> str:
    price = f" — от {sketch.price} ₽" if sketch.price else " — цена договорная"
    return f"{sketch.name}{price}"


async def _send_styles_page(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    current_page: int,
    step: int,
) -> None:
    service = SketchCatalogService(session=session)
    styles = await service.get_styles()

    if not styles:
        await state.clear()
        await message.answer(
            "К сожалению, список стилей пока пуст.",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    page = _shift_page(
        current_page=current_page,
        step=step,
        items_count=len(styles),
    )
    style_buttons = _build_style_buttons(styles=styles, page=page)

    await state.update_data(style_buttons=style_buttons, style_page=page)
    await state.set_state(SketchCatalogState.choosing_style)
    await message.answer(
        _build_page_text(title="Выберите стиль", page=page, items_count=len(styles)),
        reply_markup=build_styles_reply_keyboard(styles=styles, page=page),
    )


async def _send_sketches_page(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
    current_page: int,
    step: int,
) -> None:
    data = await state.get_data()
    style_id = data.get("style_id")

    if not style_id:
        await state.clear()
        await message.answer(
            "Не удалось открыть список эскизов. Откройте каталог заново.",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    service = SketchCatalogService(session=session)
    sketches = await service.get_sketches_by_style_id(style_id=int(style_id))

    if not sketches:
        await state.clear()
        await message.answer(
            "В этом стиле пока нет доступных эскизов.",
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    page = _shift_page(
        current_page=current_page,
        step=step,
        items_count=len(sketches),
    )
    sketch_buttons = _build_sketch_buttons(sketches=sketches, page=page)

    await state.update_data(sketch_buttons=sketch_buttons, sketch_page=page)
    await state.set_state(SketchCatalogState.choosing_sketch)
    await message.answer(
        _build_page_text(title="Выберите эскиз", page=page, items_count=len(sketches)),
        reply_markup=build_sketches_reply_keyboard(sketches=sketches, page=page),
    )


def _build_style_buttons(styles, page: int) -> dict[str, int]:
    page_styles = _get_page_items(items=styles, page=page)
    return {style.name: style.id for style in page_styles}


def _build_sketch_buttons(sketches, page: int) -> dict[str, int]:
    page_sketches = _get_page_items(items=sketches, page=page)
    return {_build_sketch_button_text(sketch): sketch.id for sketch in page_sketches}


def _get_page_items(items, page: int):
    start = page * CATALOG_PAGE_SIZE
    return items[start : start + CATALOG_PAGE_SIZE]


def _shift_page(current_page: int, step: int, items_count: int) -> int:
    last_page = max((items_count - 1) // CATALOG_PAGE_SIZE, 0)
    return min(max(current_page + step, 0), last_page)


def _build_page_text(title: str, page: int, items_count: int) -> str:
    last_page = max((items_count - 1) // CATALOG_PAGE_SIZE, 0)
    return f"{title}: страница {page + 1} из {last_page + 1}"
