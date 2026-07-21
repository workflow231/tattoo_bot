from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError

from bot.handlers.admin_appointments import _send_admin_appointment_card
from bot.handlers.admin_calendar import _send_client_sketch_photo
from services.sketch_catalog_service import SketchCatalogService


@pytest.mark.anyio
async def test_selected_sketch_card_falls_back_when_photo_is_invalid() -> None:
    bad_file_id = "invalid-photo-file-id"
    sketch = SimpleNamespace(
        id=1,
        name="Линии",
        price=None,
        status="available",
        description=None,
        photo_file_id=bad_file_id,
        style=SimpleNamespace(name="Графика"),
    )
    message = _FakeMessage(photo_error=TelegramNetworkError(object(), "failed"))

    await SketchCatalogService(session=None).send_selected_sketch_card(
        message=message,
        sketch=sketch,
    )

    assert len(message.answers) == 1
    assert "Фото сейчас недоступно" in message.answers[0]["text"]
    assert bad_file_id not in message.answers[0]["text"]


@pytest.mark.anyio
async def test_media_group_falls_back_without_file_ids() -> None:
    bad_file_id = "invalid-media-group-file-id"
    media = [
        SimpleNamespace(media=bad_file_id, caption="Эскиз: Линии"),
        SimpleNamespace(media="another-file-id", caption="Эскиз: Точка"),
    ]
    message = _FakeMessage(
        media_group_error=TelegramAPIError(object(), "failed"),
    )

    await SketchCatalogService(session=None)._send_media(
        message=message,
        media=media,
    )

    assert len(message.answers) == 1
    assert "Не удалось показать фото" in message.answers[0]["text"]
    assert "Эскиз: Линии" in message.answers[0]["text"]
    assert bad_file_id not in message.answers[0]["text"]
    assert "another-file-id" not in message.answers[0]["text"]


@pytest.mark.anyio
async def test_admin_appointment_card_falls_back_when_client_photo_is_invalid() -> None:
    bad_file_id = "invalid-client-sketch-file-id"
    message = _FakeMessage(photo_error=TelegramNetworkError(object(), "failed"))
    service = _FakeAdminAppointmentService(photo_file_id=bad_file_id)

    await _send_admin_appointment_card(
        message=message,
        service=service,
        appointment_id=1,
        card_text="Заявка #1",
    )

    assert len(message.answers) == 2
    assert message.answers[0]["text"] == "Заявка #1"
    assert "Фото эскиза клиента сейчас недоступно." == message.answers[1]["text"]
    assert bad_file_id not in message.answers[1]["text"]


@pytest.mark.anyio
async def test_admin_calendar_card_falls_back_when_client_photo_is_invalid() -> None:
    bad_file_id = "invalid-calendar-client-sketch-file-id"
    message = _FakeMessage(photo_error=TelegramNetworkError(object(), "failed"))
    service = _FakeAdminAppointmentService(photo_file_id=bad_file_id)

    await _send_client_sketch_photo(
        message=message,
        service=service,
        appointment_id=1,
    )

    assert len(message.answers) == 1
    assert "Фото эскиза клиента сейчас недоступно." == message.answers[0]["text"]
    assert bad_file_id not in message.answers[0]["text"]


class _FakeBot:
    def __init__(self, media_group_error=None) -> None:
        self.media_group_error = media_group_error

    async def send_media_group(self, **kwargs) -> None:
        if self.media_group_error:
            raise self.media_group_error


class _FakeMessage:
    def __init__(self, photo_error=None, media_group_error=None) -> None:
        self.photo_error = photo_error
        self.answers = []
        self.photo_answers = []
        self.chat = SimpleNamespace(id=123)
        self.bot = _FakeBot(media_group_error=media_group_error)

    async def answer(self, text, **kwargs) -> None:
        self.answers.append({"text": text, **kwargs})

    async def answer_photo(self, **kwargs) -> None:
        if self.photo_error:
            raise self.photo_error

        self.photo_answers.append(kwargs)


class _FakeAdminAppointmentService:
    def __init__(self, photo_file_id: str | None) -> None:
        self.photo_file_id = photo_file_id

    async def get_client_sketch_photo_file_id(self, appointment_id: int) -> str | None:
        return self.photo_file_id
