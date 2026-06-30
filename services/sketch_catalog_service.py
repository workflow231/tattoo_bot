from aiogram.types import Message, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import (
    build_styles_reply_keyboard,
    build_sketches_reply_keyboard,
    sketch_card_kb,
)
from bot.utils.chunks import chunks
from db.models import Style, Sketch
from db.repositories.style_repo import get_all_styles
from db.repositories.sketch_repo import (
    find_viewed_sketch_photo_in_style,
    get_available_sketches_by_style_id,
    get_sketch_by_id_with_style,
)


class SketchCatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_styles(self) -> list[Style]:
        styles = await get_all_styles(session=self.session)
        return styles or []

    async def get_sketches_by_style_id(self, style_id: int) -> list[Sketch]:
        return await get_available_sketches_by_style_id(
            session=self.session,
            style_id=style_id,
        )

    async def get_sketch_by_id(self, sketch_id: int) -> Sketch | None:
        return await get_sketch_by_id_with_style(
            session=self.session,
            sketch_id=sketch_id,
        )

    async def send_styles_catalog(
        self,
        message: Message,
        styles: list[Style],
    ) -> None:
        style_cards = await self._build_style_cards(styles)

        if not style_cards:
            await message.answer(
                "Пока нет доступных эскизов для показа в каталоге."
            )
            return

        for style_chunk in chunks(style_cards, 10):
            media = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption=style.name,
                )
                for style, photo_file_id in style_chunk
            ]

            await self._send_media(message, media)

        await message.answer(
            "Выберите стиль:",
            reply_markup=build_styles_reply_keyboard(styles),
        )

    async def send_sketches_catalog(
        self,
        message: Message,
        sketches: list[Sketch],
    ) -> None:
        if not sketches:
            await message.answer("В этом стиле пока нет доступных эскизов.")
            return

        for sketch_chunk in chunks(sketches, 10):
            media = [
                InputMediaPhoto(
                    media=sketch.photo_file_id,
                    caption=self._build_short_sketch_caption(sketch),
                )
                for sketch in sketch_chunk
            ]

            await self._send_media(message, media)

        await message.answer(
            "Выберите эскиз:",
            reply_markup=build_sketches_reply_keyboard(sketches),
        )

    async def send_selected_sketch_card(
        self,
        message: Message,
        sketch: Sketch,
    ) -> None:
        await message.answer_photo(
            photo=sketch.photo_file_id,
            caption=self._build_full_sketch_caption(sketch),
            reply_markup=sketch_card_kb,
        )

    async def _build_style_cards(
        self,
        styles: list[Style],
    ) -> list[tuple[Style, str]]:
        result = []

        for style in styles:
            photo_file_id = await find_viewed_sketch_photo_in_style(
                session=self.session,
                style_id=style.id,
            )

            if photo_file_id:
                result.append((style, photo_file_id))

        return result

    async def _send_media(
        self,
        message: Message,
        media: list[InputMediaPhoto],
    ) -> None:
        if not media:
            return

        if len(media) == 1:
            item = media[0]

            await message.answer_photo(
                photo=item.media,
                caption=item.caption,
            )
            return

        await message.bot.send_media_group(
            chat_id=message.chat.id,
            media=media,
        )

    def _build_short_sketch_caption(self, sketch: Sketch) -> str:
        price = f"от {sketch.price} ₽" if sketch.price else "договорная"

        return (
            f"Эскиз: {sketch.name}\n"
            f"Цена: {price}"
        )

    def _build_full_sketch_caption(self, sketch: Sketch) -> str:
        price = f"от {sketch.price} ₽" if sketch.price else "договорная"
        status = self._format_status(sketch.status)
        description = sketch.description or "Описание не указано."
        style_name = sketch.style.name if sketch.style else "Не указан"

        return (
            f"Эскиз: {sketch.name}\n"
            f"Стиль: {style_name}\n"
            f"Цена: {price}\n"
            f"Статус: {status}\n"
            f"Описание: {description}"
        )

    def _format_status(self, status: str) -> str:
        statuses = {
            "available": "доступен",
            "reserved": "зарезервирован",
            "hidden": "скрыт",
        }

        return statuses.get(status, status)