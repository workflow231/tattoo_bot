from services.admin_sketch_service import AdminSketchService, SketchDraft


def test_admin_sketch_service_parses_fields() -> None:
    service = AdminSketchService(session=None)

    assert service.parse_optional_text("  текст  ") == "текст"
    assert service.parse_optional_text("Пропустить") is None
    assert service.parse_optional_price("12000") == 12000
    assert service.parse_optional_price("Пропустить") is None
    assert service.parse_optional_price("12к") is None
    assert service.parse_views("0") == 0
    assert service.parse_views("abc") is None
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
        views=0,
    )

    text = service.build_summary_text(draft)

    assert "Стиль: Графика" in text
    assert "Название: Линии" in text
    assert "Цена: договорная" in text
    assert "Статус: доступен" in text
