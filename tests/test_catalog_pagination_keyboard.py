from db.models import Sketch, Style
from bot.handlers.sketch_catalog_handler import _build_sketch_buttons
from bot.keyboards import (
    ADD_SKETCH_BUTTON,
    ADMIN_SKETCHES_BUTTON,
    CATALOG_BUTTON,
    CHAT_WITH_MASTER_BUTTON,
    CHOOSE_SKETCH_BUTTON,
    CREATE_REQUEST_BUTTON,
    DELETE_SKETCH_BUTTON,
    DELETE_STYLE_BUTTON,
    EDIT_SKETCH_DESCRIPTION_BUTTON,
    EDIT_SKETCH_BUTTON,
    EDIT_SKETCH_NAME_BUTTON,
    EDIT_SKETCH_PHOTO_BUTTON,
    EDIT_SKETCH_PRICE_BUTTON,
    EDIT_SKETCH_STATUS_BUTTON,
    EDIT_SKETCH_STYLE_BUTTON,
    EDIT_STYLE_BUTTON,
    MY_SKETCH_BUTTON,
    MY_SOCIALS_BUTTON,
    NEXT_PAGE_BUTTON,
    NO_SKETCH_REQUEST_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    SEND_MY_SKETCH_BUTTON,
    build_admin_sketch_actions_keyboard,
    build_admin_sketch_edit_fields_keyboard,
    build_booking_menu_keyboard,
    build_custom_sketch_menu_keyboard,
    build_sketches_reply_keyboard,
    build_styles_reply_keyboard,
    client_menu_kb,
    master_menu_kb,
    sketch_card_kb,
)


def test_styles_keyboard_paginates_after_ten_items() -> None:
    styles = [Style(id=index, name=f"Стиль {index}") for index in range(1, 12)]

    keyboard = build_styles_reply_keyboard(styles=styles, page=0)
    texts = _keyboard_texts(keyboard)

    assert "Стиль 1" in texts
    assert "Стиль 10" in texts
    assert "Стиль 11" not in texts
    assert NEXT_PAGE_BUTTON in texts
    assert PREVIOUS_PAGE_BUTTON not in texts


def test_styles_keyboard_second_page_has_previous_button() -> None:
    styles = [Style(id=index, name=f"Стиль {index}") for index in range(1, 12)]

    keyboard = build_styles_reply_keyboard(styles=styles, page=1)
    texts = _keyboard_texts(keyboard)

    assert "Стиль 11" in texts
    assert "Стиль 1" not in texts
    assert PREVIOUS_PAGE_BUTTON in texts
    assert NEXT_PAGE_BUTTON not in texts


def test_sketches_keyboard_paginates_after_ten_items() -> None:
    sketches = [
        Sketch(id=index, name=f"Эскиз {index}", price=None, style_id=1)
        for index in range(1, 12)
    ]

    keyboard = build_sketches_reply_keyboard(sketches=sketches, page=0)
    texts = _keyboard_texts(keyboard)

    assert "Эскиз 1 — цена договорная" in texts
    assert "Эскиз 10 — цена договорная" in texts
    assert "Эскиз 11 — цена договорная" not in texts
    assert NEXT_PAGE_BUTTON in texts


def test_duplicate_sketch_buttons_are_unique_on_same_page() -> None:
    sketches = [
        Sketch(id=1, name="Линии", price=None, style_id=1),
        Sketch(id=2, name="Линии", price=None, style_id=1),
    ]

    keyboard = build_sketches_reply_keyboard(sketches=sketches, page=0)
    texts = _keyboard_texts(keyboard)

    assert "Линии — цена договорная (#1)" in texts
    assert "Линии — цена договорная (#2)" in texts


def test_duplicate_sketch_buttons_map_to_stable_sketch_ids() -> None:
    sketches = [
        Sketch(id=1, name="Линии", price=None, style_id=1),
        Sketch(id=2, name="Линии", price=None, style_id=1),
    ]

    buttons = _build_sketch_buttons(sketches=sketches, page=0)

    assert buttons == {
        "Линии — цена договорная (#1)": 1,
        "Линии — цена договорная (#2)": 2,
    }


def test_master_menu_does_not_show_chat_with_master() -> None:
    assert CHAT_WITH_MASTER_BUTTON not in _keyboard_texts(master_menu_kb)


def test_main_menus_show_booking_entry() -> None:
    assert CATALOG_BUTTON in _keyboard_texts(client_menu_kb)
    assert CATALOG_BUTTON in _keyboard_texts(master_menu_kb)
    assert MY_SOCIALS_BUTTON in _keyboard_texts(client_menu_kb)
    assert "Мои соцсети" not in _keyboard_texts(client_menu_kb)
    assert "Каталог эскизов" not in _keyboard_texts(client_menu_kb)
    assert "Каталог эскизов" not in _keyboard_texts(master_menu_kb)


def test_booking_menu_shows_request_type_actions() -> None:
    texts = _keyboard_texts(build_booking_menu_keyboard())

    assert MY_SKETCH_BUTTON in texts
    assert CHOOSE_SKETCH_BUTTON in texts
    assert CHAT_WITH_MASTER_BUTTON in texts
    assert NO_SKETCH_REQUEST_BUTTON in texts


def test_custom_sketch_menu_shows_photo_action() -> None:
    texts = _keyboard_texts(build_custom_sketch_menu_keyboard())

    assert SEND_MY_SKETCH_BUTTON in texts
    assert CHAT_WITH_MASTER_BUTTON in texts


def test_master_menu_shows_sketches_section_instead_of_direct_add_button() -> None:
    texts = _keyboard_texts(master_menu_kb)

    assert ADMIN_SKETCHES_BUTTON in texts
    assert ADD_SKETCH_BUTTON not in texts


def test_admin_sketch_actions_keyboard_shows_management_buttons() -> None:
    texts = _keyboard_texts(build_admin_sketch_actions_keyboard())

    assert ADD_SKETCH_BUTTON in texts
    assert DELETE_STYLE_BUTTON in texts
    assert EDIT_STYLE_BUTTON in texts
    assert DELETE_SKETCH_BUTTON in texts
    assert EDIT_SKETCH_BUTTON in texts


def test_admin_sketch_edit_fields_keyboard_shows_editable_fields() -> None:
    texts = _keyboard_texts(build_admin_sketch_edit_fields_keyboard())

    assert EDIT_SKETCH_NAME_BUTTON in texts
    assert EDIT_SKETCH_DESCRIPTION_BUTTON in texts
    assert EDIT_SKETCH_PRICE_BUTTON in texts
    assert EDIT_SKETCH_PHOTO_BUTTON in texts
    assert EDIT_SKETCH_STATUS_BUTTON in texts
    assert EDIT_SKETCH_STYLE_BUTTON in texts


def test_sketch_card_does_not_show_leave_comment_button() -> None:
    texts = _keyboard_texts(sketch_card_kb)

    assert CREATE_REQUEST_BUTTON in texts
    assert "💬 Оставить комментарий" not in texts


def _keyboard_texts(keyboard) -> list[str]:
    return [button.text for row in keyboard.keyboard for button in row]
