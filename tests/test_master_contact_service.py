from services.master_contact_service import MasterContactService


def test_master_contact_text_uses_env_value(monkeypatch) -> None:
    monkeypatch.setenv("MASTER_CONTACT", "@master")

    assert (
        MasterContactService().get_contact_text() == "Связаться с мастером:\n\n@master"
    )


def test_master_contact_text_handles_missing_value(monkeypatch) -> None:
    monkeypatch.delenv("MASTER_CONTACT", raising=False)

    assert (
        "Контакт мастера пока не указан." in MasterContactService().get_contact_text()
    )
