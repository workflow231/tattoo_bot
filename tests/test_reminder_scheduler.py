from datetime import datetime, timezone

from utils.reminder_time import seconds_until_next_reminder_run


def test_seconds_until_next_run_uses_today_before_noon(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", "Europe/Moscow")
    now = datetime(2026, 7, 1, 11, 30)

    assert seconds_until_next_reminder_run(now=now) == 30 * 60


def test_seconds_until_next_run_uses_tomorrow_after_noon(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", "Europe/Moscow")
    now = datetime(2026, 7, 1, 12, 30)

    assert seconds_until_next_reminder_run(now=now) == 23.5 * 60 * 60


def test_seconds_until_next_run_converts_aware_datetime_to_bot_timezone(
    monkeypatch,
) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", "Europe/Moscow")
    now = datetime(2026, 7, 1, 8, 30, tzinfo=timezone.utc)

    assert seconds_until_next_reminder_run(now=now) == 30 * 60
