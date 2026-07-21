from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    BACK_BUTTON,
    CATALOG_PAGE_SIZE,
    CHAT_WITH_MASTER_BUTTON,
    CHOOSE_SKETCH_BUTTON,
    MAIN_MENU_BUTTON,
    NEXT_PAGE_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    build_sketch_button_text,
    build_sketches_reply_keyboard,
    build_styles_reply_keyboard,
    get_duplicate_sketch_button_texts,
    sketch_card_kb,
)
from bot.menu_utils import get_main_menu_for_message
from services.client_text_service import ClientTextService
from services.sketch_catalog_service import SketchCatalogService
from services.master_contact_service import MasterContactService
from bot.states import SketchCatalogState

router = Router()


@router.message(F.text == CHOOSE_SKETCH_BUTTON)
async def sketch_catalog(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    await start_sketch_catalog(message=message, state=state, session=session)


async def start_sketch_catalog(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()

    service = SketchCatalogService(session=session)

    styles = await service.get_styles()

    if not styles:
        await message.answer(
            ClientTextService().text("catalog_empty"),
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
            ClientTextService().text("main_menu"),
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
        await message.answer(ClientTextService().text("catalog_choose_style_button"))
        return

    service = SketchCatalogService(session=session)

    sketches = await service.get_sketches_by_style_id(style_id=style_id)

    if not sketches:
        await message.answer(ClientTextService().text("catalog_style_empty"))
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
            ClientTextService().text("main_menu"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == BACK_BUTTON:
        await state.clear()

        service = SketchCatalogService(session=session)

        styles = await service.get_styles()

        if not styles:
            await message.answer(
                ClientTextService().text("catalog_empty_short"),
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
        await message.answer(ClientTextService().text("catalog_choose_sketch_button"))
        return

    service = SketchCatalogService(session=session)

    sketch = await service.get_sketch_by_id(sketch_id=sketch_id)

    if not sketch:
        await message.answer(ClientTextService().text("catalog_sketch_unavailable"))
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
            ClientTextService().text("main_menu"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    if message.text == BACK_BUTTON:
        data = await state.get_data()
        style_id = data.get("style_id")

        if not style_id:
            await state.clear()
            await message.answer(
                ClientTextService().text("catalog_return_failed"),
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
                ClientTextService().text("catalog_style_empty"),
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
        ClientTextService().text("choose_action"),
        reply_markup=sketch_card_kb,
    )


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
            ClientTextService().text("catalog_empty_short"),
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
        _build_page_text(
            title=ClientTextService().text("catalog_choose_style_title"),
            page=page,
            items_count=len(styles),
        ),
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
            ClientTextService().text("catalog_open_failed"),
            reply_markup=get_main_menu_for_message(session=session, message=message),
        )
        return

    service = SketchCatalogService(session=session)
    sketches = await service.get_sketches_by_style_id(style_id=int(style_id))

    if not sketches:
        await state.clear()
        await message.answer(
            ClientTextService().text("catalog_style_empty"),
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
        _build_page_text(
            title=ClientTextService().text("catalog_choose_sketch_title"),
            page=page,
            items_count=len(sketches),
        ),
        reply_markup=build_sketches_reply_keyboard(sketches=sketches, page=page),
    )


def _build_style_buttons(styles, page: int) -> dict[str, int]:
    page_styles = _get_page_items(items=styles, page=page)
    return {style.name: style.id for style in page_styles}


def _build_sketch_buttons(sketches, page: int) -> dict[str, int]:
    page_sketches = _get_page_items(items=sketches, page=page)
    duplicate_texts = get_duplicate_sketch_button_texts(page_sketches)

    return {
        build_sketch_button_text(
            sketch=sketch,
            disambiguate=build_sketch_button_text(sketch) in duplicate_texts,
        ): sketch.id
        for sketch in page_sketches
    }


def _get_page_items(items, page: int):
    start = page * CATALOG_PAGE_SIZE
    return items[start : start + CATALOG_PAGE_SIZE]


def _shift_page(current_page: int, step: int, items_count: int) -> int:
    last_page = max((items_count - 1) // CATALOG_PAGE_SIZE, 0)
    return min(max(current_page + step, 0), last_page)


def _build_page_text(title: str, page: int, items_count: int) -> str:
    last_page = max((items_count - 1) // CATALOG_PAGE_SIZE, 0)
    return ClientTextService().format_text(
        "catalog_page_title",
        title=title,
        page=str(page + 1),
        pages=str(last_page + 1),
    )
