import json

from services.client_text_service import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_TEXTS,
    ClientTextService,
    TELEGRAM_MESSAGE_LIMIT,
)


def test_client_text_service_uses_defaults() -> None:
    service = ClientTextService()

    assert service.welcome_new_user() == "Добро пожаловать!"
    assert service.welcome_existing_user() == "С возвращением!"
    assert "Контакт мастера пока не указан." in service.master_contact_missing()
    assert "Заявка создана" in service.appointment_created()
    assert "Ваша заявка отклонена." in service.appointment_rejected()
    assert "Сессия устарела." in service.stale_session()
    assert service.my_socials() == "Соц сети еще не добавленны"
    assert service.text("booking_menu_prompt") == "Выберите вариант записи:"
    assert (
        service.format_text("appointment_choose_date", month_title="Июль 2026")
        == "Выберите дату: Июль 2026\n\n"
        "Недоступные дни отмечены символом ×."
    )


def test_client_text_config_has_all_default_keys() -> None:
    data = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))

    assert set(DEFAULT_TEXTS).issubset(data)


def test_client_text_service_supports_config_overrides(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"welcome_new_user": "Привет\nЗапишитесь онлайн"},
    )

    assert (
        ClientTextService(config_path=config_path).welcome_new_user()
        == "Привет\nЗапишитесь онлайн"
    )


def test_client_text_service_formats_master_contact(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"master_contact": "Для связи напишите сюда: {contact}"},
    )

    assert (
        ClientTextService(config_path=config_path).master_contact(contact="@master")
        == "Для связи напишите сюда: @master"
    )


def test_client_text_service_formats_dynamic_client_messages(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={
            "appointment_confirmed": (
                "Подтверждено: " "{appointment_date} {appointment_time} {sketch_name}"
            ),
            "reminder_tomorrow": (
                "Завтра: {appointment_date} {appointment_time} {sketch_name}"
            ),
        },
    )
    service = ClientTextService(config_path=config_path)

    assert (
        service.appointment_confirmed(
            appointment_date="21.07.2026",
            appointment_time="12:00",
            sketch_name="Линии",
        )
        == "Подтверждено: 21.07.2026 12:00 Линии"
    )
    assert (
        service.reminder_tomorrow(
            appointment_date="22.07.2026",
            appointment_time="14:00",
            sketch_name="Минимализм",
        )
        == "Завтра: 22.07.2026 14:00 Минимализм"
    )


def test_client_text_service_formats_generic_template(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"booking_menu_prompt": "Выберите: {kind}"},
    )

    assert (
        ClientTextService(config_path=config_path).format_text(
            "booking_menu_prompt",
            kind="запись",
        )
        == "Выберите: запись"
    )


def test_client_text_service_falls_back_on_unknown_placeholder(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"master_contact": "Связаться: {unknown}"},
    )

    assert ClientTextService(config_path=config_path).master_contact(
        contact="@master"
    ) == ("Связаться с мастером:\n\n@master")


def test_client_text_service_falls_back_on_positional_placeholder(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"master_contact": "Связаться: {}"},
    )

    assert (
        ClientTextService(config_path=config_path).master_contact(contact="@master")
        == "Связаться с мастером:\n\n@master"
    )


def test_client_text_service_falls_back_on_too_long_text(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"stale_session": "x" * (TELEGRAM_MESSAGE_LIMIT + 1)},
    )

    assert (
        ClientTextService(config_path=config_path).stale_session()
        == "Сессия устарела. Откройте нужный раздел заново."
    )


def test_client_text_service_falls_back_on_too_long_rendered_text(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"master_contact": ("x" * TELEGRAM_MESSAGE_LIMIT) + "{contact}"},
    )

    assert (
        ClientTextService(config_path=config_path).master_contact(contact="@master")
        == "Связаться с мастером:\n\n@master"
    )


def test_client_text_service_limits_too_long_fallback_render(tmp_path) -> None:
    config_path = _write_config(
        tmp_path=tmp_path,
        data={"master_contact": "Связаться: {unknown}"},
    )

    text = ClientTextService(config_path=config_path).master_contact(
        contact="x" * (TELEGRAM_MESSAGE_LIMIT + 100)
    )

    assert len(text) == TELEGRAM_MESSAGE_LIMIT
    assert text.startswith("Связаться с мастером:")


def _write_config(tmp_path, data: dict[str, str]):
    config_path = tmp_path / "client_texts.json"
    config_path.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )
    return config_path
