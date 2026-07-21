import pytest

import bot.main as bot_main
from bot.main import _get_webhook_path
from utils.config import (
    get_admin_ids_from_env,
    get_bool_env,
    get_int_env,
    get_required_env,
    get_timezone_name_env,
)


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


def test_get_int_env_rejects_non_integer(monkeypatch) -> None:
    monkeypatch.setenv("WEBHOOK_PORT", "not-a-port")

    with pytest.raises(RuntimeError, match="WEBHOOK_PORT must be an integer"):
        get_int_env("WEBHOOK_PORT", 8080)


def test_timezone_name_uses_default_for_empty_env(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", " ")

    assert get_timezone_name_env() == "Europe/Moscow"


def test_webhook_path_must_start_with_slash(monkeypatch) -> None:
    monkeypatch.setenv("WEBHOOK_PATH", "webhook")

    with pytest.raises(RuntimeError, match="WEBHOOK_PATH must start with /"):
        _get_webhook_path()


def test_webhook_path_defaults_to_webhook(monkeypatch) -> None:
    monkeypatch.delenv("WEBHOOK_PATH", raising=False)

    assert _get_webhook_path() == "/webhook"


def test_user_service_admin_ids_parse_list_and_ignore_invalid_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ADMIN_IDS", "123, invalid, 456")
    monkeypatch.setenv("ADMIN_ID", "789")

    assert get_admin_ids_from_env() == {123, 456, 789}


@pytest.mark.anyio
async def test_main_runs_migrations_before_reading_config(monkeypatch) -> None:
    events: list[str] = []

    def run_database_migrations() -> None:
        events.append("migrate")

    def get_required_env(name: str) -> str:
        events.append(f"env:{name}")
        raise RuntimeError("stop")

    monkeypatch.setattr(bot_main, "run_database_migrations", run_database_migrations)
    monkeypatch.setattr(bot_main, "get_required_env", get_required_env)

    with pytest.raises(RuntimeError, match="stop"):
        await bot_main.main()

    assert events == ["migrate", "env:BOT_TOKEN"]
