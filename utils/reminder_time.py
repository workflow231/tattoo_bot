from datetime import datetime, time, timedelta

from utils.timezone import get_bot_timezone

REMINDER_HOUR = 12
REMINDER_MINUTE = 0
REMINDER_TIME = time(hour=REMINDER_HOUR, minute=REMINDER_MINUTE)


def seconds_until_next_reminder_run(now: datetime | None = None) -> float:
    timezone = get_bot_timezone()

    if now is None:
        now = datetime.now(tz=timezone)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone)
    else:
        now = now.astimezone(timezone)

    next_run = datetime.combine(now.date(), REMINDER_TIME, tzinfo=timezone)

    if next_run <= now:
        next_run += timedelta(days=1)

    return (next_run - now).total_seconds()
