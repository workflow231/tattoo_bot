from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Sketch, Style
from db.repositories.sketch_repo import create_sketch
from db.repositories.style_repo import create_style, get_all_styles

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
    views: int


class AdminSketchService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_styles(self) -> list[Style]:
        return await get_all_styles(session=self.session) or []

    async def create_style(self, style_name: str) -> Style:
        return await create_style(
            session=self.session,
            style_name=style_name.strip(),
        )

    async def create_sketch(self, draft: SketchDraft) -> Sketch:
        return await create_sketch(
            session=self.session,
            style_id=draft.style_id,
            name=draft.name,
            description=draft.description,
            price=draft.price,
            photo_file_id=draft.photo_file_id,
            status=draft.status,
            views=draft.views,
        )

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

    def parse_views(self, value: str | None) -> int | None:
        value = (value or "").strip()

        if not value:
            return None

        if not value.isdigit():
            return None

        return int(value)

    def parse_status(self, value: str | None) -> str | None:
        return STATUS_VALUES.get((value or "").strip())

    def build_summary_text(self, draft: SketchDraft) -> str:
        description = draft.description or "Не указано"
        price = f"{draft.price} ₽" if draft.price is not None else "договорная"
        photo = draft.photo_file_id or "Не указано"

        return (
            "Проверьте эскиз:\n\n"
            f"Стиль: {draft.style_name}\n"
            f"Название: {draft.name}\n"
            f"Описание: {description}\n"
            f"Цена: {price}\n"
            f"Фото file_id: {photo}\n"
            f"Статус: {STATUS_LABELS.get(draft.status, draft.status)}\n"
            f"Просмотры: {draft.views}"
        )
