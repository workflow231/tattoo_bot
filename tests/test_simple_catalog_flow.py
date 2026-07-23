import pytest

from bot.handlers import sketch_catalog_handler
from bot.handlers import admin_sketches
from bot.keyboards import ADD_SKETCH_BUTTON, BACK_BUTTON, CATALOG_BUTTON, client_menu_kb
from bot.states import SketchCatalogState
from bot.states import AdminSketchState
from db.repositories.style_repo import INTERNAL_SIMPLE_STYLE_NAME
from db.models import Sketch, Style


class FakeMessage:
    def __init__(self, text: str, user_id: int | None = None):
        self.text = text
        self.from_user = FakeUser(user_id) if user_id is not None else None
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


class FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class FakeState:
    def __init__(self):
        self.data = {}
        self.state = None
        self.clear_called = False

    async def clear(self):
        self.clear_called = True
        self.data = {}
        self.state = None

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.state = state

    async def get_data(self):
        return self.data


class FakeCatalogService:
    sent_styles = []
    sent_sketches = []

    def __init__(self, session):
        self.session = session

    async def get_styles(self):
        return [Style(id=1, name="Маникюр")]

    async def get_sketches(self):
        return [Sketch(id=1, name="Покрытие", price=None, style_id=1)]

    async def send_styles_catalog(self, message, styles):
        self.sent_styles.append(styles)
        await message.answer("Выберите категорию:")

    async def send_sketches_catalog(self, message, sketches):
        self.sent_sketches.append(sketches)
        await message.answer("Выберите услугу:")


class FakeAdminSketchService:
    def __init__(self, session):
        self.session = session

    async def get_or_create_default_style(self):
        return Style(id=9, name=INTERNAL_SIMPLE_STYLE_NAME)


@pytest.mark.anyio
async def test_catalog_entry_uses_categories_in_full_mode(monkeypatch) -> None:
    FakeCatalogService.sent_styles = []
    FakeCatalogService.sent_sketches = []
    monkeypatch.setattr(sketch_catalog_handler, "is_simple_bot", lambda: False)
    monkeypatch.setattr(
        sketch_catalog_handler,
        "SketchCatalogService",
        FakeCatalogService,
    )
    state = FakeState()
    message = FakeMessage(CATALOG_BUTTON)

    await sketch_catalog_handler.sketch_catalog(
        message=message,
        state=state,
        session=None,
    )

    assert state.state == SketchCatalogState.choosing_style
    assert state.data["style_buttons"] == {"Маникюр": 1}
    assert FakeCatalogService.sent_styles
    assert not FakeCatalogService.sent_sketches


@pytest.mark.anyio
async def test_catalog_entry_uses_services_in_simple_mode(monkeypatch) -> None:
    FakeCatalogService.sent_styles = []
    FakeCatalogService.sent_sketches = []
    monkeypatch.setattr(sketch_catalog_handler, "is_simple_bot", lambda: True)
    monkeypatch.setattr(
        sketch_catalog_handler,
        "SketchCatalogService",
        FakeCatalogService,
    )
    state = FakeState()
    message = FakeMessage(CATALOG_BUTTON)

    await sketch_catalog_handler.sketch_catalog(
        message=message,
        state=state,
        session=None,
    )

    assert state.state == SketchCatalogState.choosing_sketch
    assert state.data["simple_bot"] is True
    assert state.data["sketch_buttons"] == {"Покрытие — цена договорная": 1}
    assert FakeCatalogService.sent_sketches
    assert not FakeCatalogService.sent_styles


@pytest.mark.anyio
async def test_back_from_simple_service_list_returns_main_menu(monkeypatch) -> None:
    monkeypatch.setattr(sketch_catalog_handler, "is_simple_bot", lambda: True)
    state = FakeState()
    state.data = {"simple_bot": True}
    message = FakeMessage(BACK_BUTTON)

    await sketch_catalog_handler.choose_sketch(
        message=message,
        state=state,
        session=None,
    )

    assert state.clear_called is True
    assert message.answers == [("Главное меню", client_menu_kb)]


@pytest.mark.anyio
async def test_back_from_stale_category_service_list_uses_simple_mode(
    monkeypatch,
) -> None:
    monkeypatch.setattr(sketch_catalog_handler, "is_simple_bot", lambda: True)
    state = FakeState()
    state.data = {"style_id": 1}
    message = FakeMessage(BACK_BUTTON)

    await sketch_catalog_handler.choose_sketch(
        message=message,
        state=state,
        session=None,
    )

    assert state.clear_called is True
    assert message.answers == [("Главное меню", client_menu_kb)]


@pytest.mark.anyio
async def test_admin_add_service_skips_categories_in_simple_mode(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    monkeypatch.setattr(admin_sketches, "is_simple_bot", lambda: True)
    monkeypatch.setattr(
        admin_sketches,
        "AdminSketchService",
        FakeAdminSketchService,
    )
    state = FakeState()
    message = FakeMessage(ADD_SKETCH_BUTTON, user_id=123)

    await admin_sketches.choose_admin_sketch_action(
        message=message,
        state=state,
        session=None,
    )

    assert state.state == AdminSketchState.waiting_name
    assert state.data["admin_sketch_style_id"] == 9
    assert state.data["admin_sketch_style_name"] == INTERNAL_SIMPLE_STYLE_NAME
    assert message.answers[0][0] == "Введите название услуги:"


@pytest.mark.anyio
async def test_admin_stale_category_selection_skips_categories_in_simple_mode(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    monkeypatch.setattr(admin_sketches, "is_simple_bot", lambda: True)
    monkeypatch.setattr(
        admin_sketches,
        "AdminSketchService",
        FakeAdminSketchService,
    )
    state = FakeState()
    state.data = {"admin_sketch_style_buttons": {"Маникюр": 1}}
    message = FakeMessage("Маникюр", user_id=123)

    await admin_sketches.choose_sketch_style(
        message=message,
        state=state,
        session=None,
    )

    assert state.state == AdminSketchState.waiting_name
    assert state.data["admin_sketch_style_id"] == 9
    assert message.answers[0][0] == "Введите название услуги:"


@pytest.mark.anyio
async def test_admin_stale_style_management_returns_services_menu(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123")
    monkeypatch.setattr(admin_sketches, "is_simple_bot", lambda: True)
    state = FakeState()
    state.data = {"admin_style_buttons": {"Маникюр": 1}}
    message = FakeMessage("Маникюр", user_id=123)

    await admin_sketches._handle_style_management_selection(
        message=message,
        state=state,
        session=None,
        action=admin_sketches.ACTION_EDIT_STYLE,
        target_state=AdminSketchState.choosing_style_to_edit,
    )

    assert state.state == AdminSketchState.choosing_action
    assert message.answers[0][0] == "Выберите действие с услугами:"
