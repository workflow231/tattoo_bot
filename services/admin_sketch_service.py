from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Sketch, Style
from db.repositories.sketch_repo import (
    count_appointments_by_sketch_id,
    create_sketch,
    delete_sketch,
    get_all_sketches_with_style,
    get_sketch_by_id_with_style,
    update_sketch,
)
from db.repositories.style_repo import (
    count_appointments_by_style_id,
    count_sketches_by_style_id,
    create_style,
    delete_style_with_sketches,
    get_all_styles,
    get_style_by_id,
    get_style_by_name,
    update_style_name,
)

STATUS_LABELS = {
    "available": "доступен",
    "reserved": "зарезервирован",
    "hidden": "скрыт",
}

STATUS_VALUES = {
    "Доступен": "available",
    "Зарезервирован": "reserved",
    "Скрыт": "hidden",
}


@dataclass(frozen=True)
class SketchDraft:
    style_id: int
    style_name: str
    name: str
    description: str | None
    price: int | None
    photo_file_id: str | None
    status: str


class AdminSketchService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_styles(self) -> list[Style]:
        return await get_all_styles(session=self.session) or []

    async def get_sketches(self) -> list[Sketch]:
        return await get_all_sketches_with_style(session=self.session)

    async def get_sketch(self, sketch_id: int) -> Sketch | None:
        return await get_sketch_by_id_with_style(
            session=self.session,
            sketch_id=sketch_id,
        )

    async def create_style(self, style_name: str) -> Style:
        return await create_style(
            session=self.session,
            style_name=style_name.strip(),
        )

    async def rename_style(self, style_id: int, style_name: str) -> str:
        style_name = style_name.strip()

        if not style_name:
            return "Название стиля не может быть пустым."

        style = await get_style_by_id(session=self.session, style_id=style_id)

        if not style:
            return "Стиль не найден."

        existing_style = await get_style_by_name(
            session=self.session,
            style_name=style_name,
        )

        if existing_style and existing_style.id != style.id:
            return "Стиль с таким названием уже существует."

        updated_style = await update_style_name(
            session=self.session,
            style_id=style.id,
            style_name=style_name,
        )

        if not updated_style:
            return "Стиль не найден."

        return f"Стиль переименован: {updated_style.name}."

    async def delete_style(self, style_id: int) -> str:
        style = await get_style_by_id(session=self.session, style_id=style_id)

        if not style:
            return "Стиль не найден."

        sketches_count = await count_sketches_by_style_id(
            session=self.session,
            style_id=style.id,
        )
        appointments_count = await count_appointments_by_style_id(
            session=self.session,
            style_id=style.id,
        )

        if appointments_count:
            return "Нельзя удалить стиль, потому что по его эскизам есть заявки."

        try:
            deleted_sketches_count, deleted = await delete_style_with_sketches(
                session=self.session,
                style_id=style.id,
            )
        except IntegrityError:
            await self.session.rollback()
            return "Нельзя удалить стиль, потому что по его эскизам есть заявки."

        if not deleted:
            return "Стиль не найден."

        if sketches_count:
            return (
                f"Стиль «{style.name}» удалён. "
                f"Удалено эскизов: {deleted_sketches_count}."
            )

        return f"Стиль «{style.name}» удалён."

    async def create_sketch(self, draft: SketchDraft) -> Sketch:
        return await create_sketch(
            session=self.session,
            style_id=draft.style_id,
            name=draft.name,
            description=draft.description,
            price=draft.price,
            photo_file_id=draft.photo_file_id,
            status=draft.status,
        )

    async def delete_sketch(self, sketch_id: int) -> str:
        sketch = await get_sketch_by_id_with_style(
            session=self.session,
            sketch_id=sketch_id,
        )

        if not sketch:
            return "Эскиз не найден."

        appointments_count = await count_appointments_by_sketch_id(
            session=self.session,
            sketch_id=sketch.id,
        )

        if appointments_count:
            return "Нельзя удалить эскиз, потому что по нему есть заявки."

        deleted = await delete_sketch(session=self.session, sketch_id=sketch.id)

        if not deleted:
            return "Эскиз не найден."

        return f"Эскиз «{sketch.name}» удалён."

    async def update_sketch_name(self, sketch_id: int, name: str) -> str:
        name = name.strip()

        if not name:
            return "Название эскиза не может быть пустым."

        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            name=name,
        )
        return self._build_sketch_update_result(sketch=sketch)

    async def update_sketch_description(
        self,
        sketch_id: int,
        description: str | None,
    ) -> str:
        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            description=description,
        )
        return self._build_sketch_update_result(sketch=sketch)

    async def update_sketch_price(self, sketch_id: int, price: int | None) -> str:
        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            price=price,
        )
        return self._build_sketch_update_result(sketch=sketch)

    async def update_sketch_photo(
        self,
        sketch_id: int,
        photo_file_id: str | None,
    ) -> str:
        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            photo_file_id=photo_file_id,
        )
        return self._build_sketch_update_result(sketch=sketch)

    async def update_sketch_status(self, sketch_id: int, status: str) -> str:
        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            status=status,
        )
        return self._build_sketch_update_result(sketch=sketch)

    async def update_sketch_style(self, sketch_id: int, style_id: int) -> str:
        style = await get_style_by_id(session=self.session, style_id=style_id)

        if not style:
            return "Стиль не найден."

        sketch = await update_sketch(
            session=self.session,
            sketch_id=sketch_id,
            style_id=style.id,
        )
        return self._build_sketch_update_result(sketch=sketch)

    def parse_optional_text(self, value: str | None) -> str | None:
        value = (value or "").strip()

        if not value or value == "Пропустить":
            return None

        return value

    def parse_optional_price(self, value: str | None) -> int | None:
        value = (value or "").strip()

        if not value or value == "Пропустить":
            return None

        if not value.isdigit():
            return None

        return int(value)

    def parse_status(self, value: str | None) -> str | None:
        return STATUS_VALUES.get((value or "").strip())

    def build_summary_text(self, draft: SketchDraft) -> str:
        description = draft.description or "Не указано"
        price = f"{draft.price} ₽" if draft.price is not None else "договорная"
        photo = self._format_photo_status(draft.photo_file_id)

        return (
            "Проверьте эскиз:\n\n"
            f"Стиль: {draft.style_name}\n"
            f"Название: {draft.name}\n"
            f"Описание: {description}\n"
            f"Цена: {price}\n"
            f"Фото: {photo}\n"
            f"Статус: {STATUS_LABELS.get(draft.status, draft.status)}"
        )

    def build_style_delete_confirmation_text(self, style_name: str) -> str:
        return f"Удалить стиль «{style_name}» и все его эскизы?"

    def build_sketch_delete_confirmation_text(self, sketch: Sketch) -> str:
        return f"Удалить эскиз «{sketch.name}»?"

    def build_sketch_card_text(self, sketch: Sketch) -> str:
        style_name = sketch.style.name if sketch.style else "Не указан"
        description = sketch.description or "Не указано"
        price = f"{sketch.price} ₽" if sketch.price is not None else "договорная"
        photo = self._format_photo_status(sketch.photo_file_id)

        return (
            f"Эскиз #{sketch.id}\n\n"
            f"Стиль: {style_name}\n"
            f"Название: {sketch.name}\n"
            f"Описание: {description}\n"
            f"Цена: {price}\n"
            f"Фото: {photo}\n"
            f"Статус: {STATUS_LABELS.get(sketch.status, sketch.status)}"
        )

    def _build_sketch_update_result(self, sketch: Sketch | None) -> str:
        if not sketch:
            return "Эскиз не найден."

        return "Эскиз обновлён.\n\n" + self.build_sketch_card_text(sketch)

    def _format_photo_status(self, photo_file_id: str | None) -> str:
        return "задано" if photo_file_id else "не задано"
