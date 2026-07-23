import pytest

from db.repositories.style_repo import INTERNAL_SIMPLE_STYLE_NAME
from services.admin_sketch_service import AdminSketchService, SketchDraft


def test_admin_sketch_service_parses_fields() -> None:
    service = AdminSketchService(session=None)

    assert service.parse_optional_text("  текст  ") == "текст"
    assert service.parse_optional_text("Пропустить") is None
    assert service.parse_optional_price("12000") == 12000
    assert service.parse_optional_price("Пропустить") is None
    assert service.parse_optional_price("12к") is None
    assert service.parse_status("Доступен") == "available"


def test_admin_sketch_service_builds_summary() -> None:
    service = AdminSketchService(session=None)
    draft = SketchDraft(
        style_id=1,
        style_name="Графика",
        name="Линии",
        description=None,
        price=None,
        photo_file_id=None,
        status="available",
    )

    text = service.build_summary_text(draft)

    assert "Категория: Графика" in text
    assert "Название: Линии" in text
    assert "Цена: договорная" in text
    assert "Фото: не задано" in text
    assert "Статус: доступен" in text
    assert "Просмотры" not in text
    assert "file_id" not in text


def test_admin_sketch_service_hides_category_in_simple_mode(monkeypatch) -> None:
    monkeypatch.setenv("SIMPLE_BOT", "true")
    service = AdminSketchService(session=None)
    draft = SketchDraft(
        style_id=1,
        style_name="Графика",
        name="Линии",
        description=None,
        price=None,
        photo_file_id="photo",
        status="available",
    )

    text = service.build_summary_text(draft)

    assert "Категория:" not in text
    assert "услугу" in text
    assert "Фото: задано" in text


def test_admin_sketch_service_hides_internal_category_name(monkeypatch) -> None:
    monkeypatch.setenv("SIMPLE_BOT", "false")
    service = AdminSketchService(session=None)
    draft = SketchDraft(
        style_id=1,
        style_name=INTERNAL_SIMPLE_STYLE_NAME,
        name="Покрытие",
        description=None,
        price=None,
        photo_file_id=None,
        status="available",
    )

    text = service.build_summary_text(draft)

    assert INTERNAL_SIMPLE_STYLE_NAME not in text
    assert "Категория:" not in text


@pytest.mark.anyio
async def test_delete_style_removes_linked_sketches(monkeypatch) -> None:
    async def fake_get_style_by_id(session, style_id):
        return type("StyleStub", (), {"id": style_id, "name": "Графика"})()

    async def fake_count_sketches_by_style_id(session, style_id):
        return 2

    async def fake_count_appointments_by_style_id(session, style_id):
        return 0

    async def fake_delete_style_with_sketches(session, style_id):
        return 2, True

    monkeypatch.setattr(
        "services.admin_sketch_service.get_style_by_id",
        fake_get_style_by_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.count_sketches_by_style_id",
        fake_count_sketches_by_style_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.count_appointments_by_style_id",
        fake_count_appointments_by_style_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.delete_style_with_sketches",
        fake_delete_style_with_sketches,
    )

    result = await AdminSketchService(session=None).delete_style(style_id=1)

    assert result == "Категория «Графика» удалена. Удалено услуг: 2."


@pytest.mark.anyio
async def test_delete_style_rejects_style_with_sketch_appointments(
    monkeypatch,
) -> None:
    async def fake_get_style_by_id(session, style_id):
        return type("StyleStub", (), {"id": style_id, "name": "Графика"})()

    async def fake_count_sketches_by_style_id(session, style_id):
        return 2

    async def fake_count_appointments_by_style_id(session, style_id):
        return 1

    monkeypatch.setattr(
        "services.admin_sketch_service.get_style_by_id",
        fake_get_style_by_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.count_sketches_by_style_id",
        fake_count_sketches_by_style_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.count_appointments_by_style_id",
        fake_count_appointments_by_style_id,
    )

    result = await AdminSketchService(session=None).delete_style(style_id=1)

    assert result == "Нельзя удалить категорию, потому что по её услугам есть заявки."


@pytest.mark.anyio
async def test_delete_sketch_rejects_sketch_with_appointments(monkeypatch) -> None:
    async def fake_get_sketch_by_id_with_style(session, sketch_id):
        return type("SketchStub", (), {"id": sketch_id, "name": "Линии"})()

    async def fake_count_appointments_by_sketch_id(session, sketch_id):
        return 1

    monkeypatch.setattr(
        "services.admin_sketch_service.get_sketch_by_id_with_style",
        fake_get_sketch_by_id_with_style,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.count_appointments_by_sketch_id",
        fake_count_appointments_by_sketch_id,
    )

    result = await AdminSketchService(session=None).delete_sketch(sketch_id=1)

    assert result == "Нельзя удалить услугу, потому что по ней есть заявки."


@pytest.mark.anyio
async def test_rename_style_rejects_duplicate_name(monkeypatch) -> None:
    async def fake_get_style_by_id(session, style_id):
        return type("StyleStub", (), {"id": style_id, "name": "Графика"})()

    async def fake_get_style_by_name(session, style_name):
        return type("StyleStub", (), {"id": 2, "name": style_name})()

    monkeypatch.setattr(
        "services.admin_sketch_service.get_style_by_id",
        fake_get_style_by_id,
    )
    monkeypatch.setattr(
        "services.admin_sketch_service.get_style_by_name",
        fake_get_style_by_name,
    )

    result = await AdminSketchService(session=None).rename_style(
        style_id=1,
        style_name="Минимализм",
    )

    assert result == "Категория с таким названием уже существует."


@pytest.mark.anyio
async def test_simple_mode_default_style_uses_internal_name(monkeypatch) -> None:
    calls = []

    async def fake_create_style(session, style_name):
        calls.append(style_name)
        return type("StyleStub", (), {"id": 1, "name": style_name})()

    monkeypatch.setattr("services.admin_sketch_service.create_style", fake_create_style)

    style = await AdminSketchService(session=None).get_or_create_default_style()

    assert style.name == INTERNAL_SIMPLE_STYLE_NAME
    assert calls == [INTERNAL_SIMPLE_STYLE_NAME]
