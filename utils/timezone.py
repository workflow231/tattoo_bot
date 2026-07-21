from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from utils.config import DEFAULT_BOT_TIMEZONE, get_timezone_name_env


def get_bot_timezone() -> tzinfo:
    timezone_name = get_timezone_name_env()

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        try:
            return ZoneInfo(DEFAULT_BOT_TIMEZONE)
        except ZoneInfoNotFoundError:
            return timezone(timedelta(hours=3), name=DEFAULT_BOT_TIMEZONE)


def now_in_bot_timezone() -> datetime:
    return datetime.now(tz=get_bot_timezone())


def today_in_bot_timezone(now: datetime | None = None) -> date:
    if now is None:
        return now_in_bot_timezone().date()

    timezone = get_bot_timezone()

    if now.tzinfo is None:
        return now.replace(tzinfo=timezone).date()

    return now.astimezone(timezone).date()
