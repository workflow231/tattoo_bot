from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    menu_kb,
    BACK_BUTTON,
    MAIN_MENU_BUTTON,
)
from services.sketch_catalog_service import SketchCatalogService
from bot.states import SketchCatalogState

router = Router()


@router.message(F.text == "Каталог эскизов")
async def sketch_catalog(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
):
    await state.clear()

    service = SketchCatalogService(session=session)

    styles = await service.get_styles()

    if not styles:
        await message.answer(
            "К сожалению, список стилей пока пуст, но он обязательно скоро появится.",
            reply_markup=menu_kb,
        )
        return

    style_buttons = {
        style.name: style.id
        for style in styles
    }

    await state.update_data(style_buttons=style_buttons)
    await state.set_state(SketchCatalogState.choosing_style)

    await service.send_styles_catalog(
        message=message,
        styles=styles,
    )


@router.message(SketchCatalogState.choosing_style)
async def choose_style(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    data = await state.get_data()
    style_buttons: dict[str, int] = data.get("style_buttons", {})

    style_id = style_buttons.get(message.text)

    if not style_id:
        await message.answer("Выберите стиль кнопкой из списка.")
        return

    service = SketchCatalogService(session=session)

    sketches = await service.get_sketches_by_style_id(style_id=style_id)

    if not sketches:
        await message.answer("В этом стиле пока нет доступных эскизов.")
        return

    sketch_buttons = {
        _build_sketch_button_text(sketch): sketch.id
        for sketch in sketches
    }

    await state.update_data(
        style_id=style_id,
        sketch_buttons=sketch_buttons,
    )
    await state.set_state(SketchCatalogState.choosing_sketch)

    await service.send_sketches_catalog(
        message=message,
        sketches=sketches,
    )


@router.message(SketchCatalogState.choosing_sketch)
async def choose_sketch(
    session: AsyncSession,
    message: Message,
    state: FSMContext,
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if message.text == BACK_BUTTON:
        await state.clear()

        service = SketchCatalogService(session=session)

        styles = await service.get_styles()

        if not styles:
            await message.answer(
                "К сожалению, список стилей пока пуст.",
                reply_markup=menu_kb,
            )
            return

        style_buttons = {
            style.name: style.id
            for style in styles
        }

        await state.update_data(style_buttons=style_buttons)
        await state.set_state(SketchCatalogState.choosing_style)

        await service.send_styles_catalog(
            message=message,
            styles=styles,
        )
        return

    data = await state.get_data()
    sketch_buttons: dict[str, int] = data.get("sketch_buttons", {})

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
):
    if message.text == MAIN_MENU_BUTTON:
        await state.clear()
        await message.answer("Главное меню", reply_markup=menu_kb)
        return

    if message.text == BACK_BUTTON:
        await state.set_state(SketchCatalogState.choosing_sketch)
        await message.answer("Вернитесь к выбору эскиза кнопками выше.")
        return

    await message.answer("Этот раздел пока не реализован.")


def _build_sketch_button_text(sketch) -> str:
    price = f" — от {sketch.price} ₽" if sketch.price else " — цена договорная"
    return f"{sketch.name}{price}"