import pytest

from utils.config import get_admin_ids_from_env, get_bool_env, get_required_env


def test_get_required_env_raises_without_value(monkeypatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="BOT_TOKEN is required"):
        get_required_env("BOT_TOKEN")


def test_get_required_env_returns_value(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")

    assert get_required_env("BOT_TOKEN") == "test-token"


def test_sql_echo_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("SQL_ECHO", raising=False)

    assert get_bool_env("SQL_ECHO", default=False) is False


def test_sql_echo_accepts_explicit_truthy_values(monkeypatch) -> None:
    monkeypatch.setenv("SQL_ECHO", "true")

    assert get_bool_env("SQL_ECHO", default=False) is True


def test_user_service_admin_ids_parse_list_and_ignore_invalid_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123, invalid, 456")
    monkeypatch.setenv("ADMIN_ID", "789")

    assert get_admin_ids_from_env() == {123, 456, 789}
