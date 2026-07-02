from datetime import datetime, time, timedelta

REMINDER_HOUR = 12
REMINDER_MINUTE = 0
REMINDER_TIME = time(hour=REMINDER_HOUR, minute=REMINDER_MINUTE)


def seconds_until_next_reminder_run(now: datetime | None = None) -> float:
    now = now or datetime.now()
    next_run = datetime.combine(now.date(), REMINDER_TIME)

    if next_run <= now:
        next_run += timedelta(days=1)

    return (next_run - now).total_seconds()
