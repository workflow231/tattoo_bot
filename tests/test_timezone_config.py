from datetime import date, datetime, timezone

import pytest

from services.reminder_service import ReminderService
from utils.timezone import get_bot_timezone, today_in_bot_timezone


def test_today_in_bot_timezone_uses_configured_timezone_boundary(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", "Europe/Moscow")
    utc_evening = datetime(2026, 7, 1, 21, 30, tzinfo=timezone.utc)

    assert today_in_bot_timezone(now=utc_evening) == date(2026, 7, 2)


def test_bot_timezone_falls_back_when_env_is_invalid(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TIMEZONE", "Invalid/Timezone")

    assert get_bot_timezone().key == "Europe/Moscow"


@pytest.mark.anyio
async def test_reminders_use_bot_timezone_today(monkeypatch) -> None:
    captured = {}

    async def fake_list_tomorrow_confirmed_without_reminder(session, tomorrow):
        captured["tomorrow"] = tomorrow
        return []

    monkeypatch.setattr(
        "services.reminder_service.today_in_bot_timezone",
        lambda: date(2026, 7, 2),
    )
    monkeypatch.setattr(
        "services.reminder_service.list_tomorrow_confirmed_without_reminder",
        fake_list_tomorrow_confirmed_without_reminder,
    )

    sent_count = await ReminderService(session=None, bot=None).send_tomorrow_reminders()

    assert sent_count == 0
    assert captured["tomorrow"] == date(2026, 7, 3)
