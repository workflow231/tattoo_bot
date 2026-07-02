from datetime import datetime

from utils.reminder_time import seconds_until_next_reminder_run


def test_seconds_until_next_run_uses_today_before_noon() -> None:
    now = datetime(2026, 7, 1, 11, 30)

    assert seconds_until_next_reminder_run(now=now) == 30 * 60


def test_seconds_until_next_run_uses_tomorrow_after_noon() -> None:
    now = datetime(2026, 7, 1, 12, 30)

    assert seconds_until_next_reminder_run(now=now) == 23.5 * 60 * 60
