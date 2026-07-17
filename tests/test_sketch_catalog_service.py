import pytest

from services.sketch_catalog_service import SketchCatalogService


@pytest.mark.anyio
async def test_get_sketch_by_id_increments_views(monkeypatch) -> None:
    calls = []
    sketch = type(
        "SketchStub",
        (),
        {"id": 7, "views": 2, "status": "available", "photo_file_id": "photo"},
    )()

    async def fake_get_sketch_by_id_with_style(session, sketch_id):
        calls.append(("get", sketch_id))
        return sketch

    async def fake_increment_sketch_views(session, sketch_id):
        calls.append(("increment", sketch_id))

    monkeypatch.setattr(
        "services.sketch_catalog_service.get_sketch_by_id_with_style",
        fake_get_sketch_by_id_with_style,
    )
    monkeypatch.setattr(
        "services.sketch_catalog_service.increment_sketch_views",
        fake_increment_sketch_views,
    )

    result = await SketchCatalogService(session=None).get_sketch_by_id(sketch_id=7)

    assert result is sketch
    assert sketch.views == 3
    assert calls == [("get", 7), ("increment", 7)]


@pytest.mark.anyio
async def test_get_sketch_by_id_does_not_increment_missing_sketch(monkeypatch) -> None:
    calls = []

    async def fake_get_sketch_by_id_with_style(session, sketch_id):
        return None

    async def fake_increment_sketch_views(session, sketch_id):
        calls.append(sketch_id)

    monkeypatch.setattr(
        "services.sketch_catalog_service.get_sketch_by_id_with_style",
        fake_get_sketch_by_id_with_style,
    )
    monkeypatch.setattr(
        "services.sketch_catalog_service.increment_sketch_views",
        fake_increment_sketch_views,
    )

    result = await SketchCatalogService(session=None).get_sketch_by_id(sketch_id=7)

    assert result is None
    assert calls == []


@pytest.mark.anyio
async def test_get_sketch_by_id_does_not_increment_unavailable_sketch(
    monkeypatch,
) -> None:
    calls = []
    sketch = type(
        "SketchStub",
        (),
        {"id": 7, "views": 2, "status": "hidden", "photo_file_id": "photo"},
    )()

    async def fake_get_sketch_by_id_with_style(session, sketch_id):
        return sketch

    async def fake_increment_sketch_views(session, sketch_id):
        calls.append(sketch_id)

    monkeypatch.setattr(
        "services.sketch_catalog_service.get_sketch_by_id_with_style",
        fake_get_sketch_by_id_with_style,
    )
    monkeypatch.setattr(
        "services.sketch_catalog_service.increment_sketch_views",
        fake_increment_sketch_views,
    )

    result = await SketchCatalogService(session=None).get_sketch_by_id(sketch_id=7)

    assert result is None
    assert sketch.views == 2
    assert calls == []
