from calendar import Calendar
from datetime import date

MONTH_NAMES = (
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)

WEEKDAY_NAMES = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
)


def build_month_weeks(
    year: int,
    month: int,
    counts_by_day: dict[date, int],
    day_off_dates: set[date] | None = None,
    blocked_slot_dates: set[date] | None = None,
) -> list[list[str]]:
    weeks = []
    day_off_dates = day_off_dates or set()
    blocked_slot_dates = blocked_slot_dates or set()

    for week in iter_month_weeks(year=year, month=month):
        week_buttons = []

        for day in week:
            appointment_count = counts_by_day.get(day, 0)
            label = str(day.day)

            if day in day_off_dates:
                label = f"{label} ×"

            if day in blocked_slot_dates:
                label = f"{label} •"

            if appointment_count:
                label = f"{label} · {appointment_count}"

            week_buttons.append(label)

        weeks.append(week_buttons)

    return weeks


def iter_month_weeks(year: int, month: int) -> list[list[date]]:
    return [
        [day for day in week if day.month == month]
        for week in Calendar(firstweekday=0).monthdatescalendar(year, month)
    ]


def shift_month(year: int, month: int, step: int) -> tuple[int, int]:
    month_index = year * 12 + month - 1 + step
    return month_index // 12, month_index % 12 + 1


def format_weekday_name(weekday: int) -> str:
    return WEEKDAY_NAMES[weekday]
