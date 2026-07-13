from db.models import Sketch, Style
from bot.keyboards import (
    CHAT_WITH_MASTER_BUTTON,
    NEXT_PAGE_BUTTON,
    PREVIOUS_PAGE_BUTTON,
    build_sketches_reply_keyboard,
    build_styles_reply_keyboard,
    master_menu_kb,
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


def test_master_menu_does_not_show_chat_with_master() -> None:
    assert CHAT_WITH_MASTER_BUTTON not in _keyboard_texts(master_menu_kb)


def _keyboard_texts(keyboard) -> list[str]:
    return [button.text for row in keyboard.keyboard for button in row]
