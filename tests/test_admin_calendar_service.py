from datetime import date

from utils.admin_calendar import build_month_weeks, format_weekday_name, shift_month


def test_build_weeks_adds_appointment_counts() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={
            date(2026, 7, 5): 3,
            date(2026, 7, 15): 1,
        },
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 · 3" in flattened_days
    assert "15 · 1" in flattened_days
    assert "1" in flattened_days


def test_build_weeks_marks_day_offs() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={date(2026, 7, 5): 3},
        day_off_dates={date(2026, 7, 5), date(2026, 7, 6)},
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 × · 3" in flattened_days
    assert "6 ×" in flattened_days


def test_build_weeks_marks_blocked_slot_days() -> None:
    weeks = build_month_weeks(
        year=2026,
        month=7,
        counts_by_day={date(2026, 7, 5): 3},
        blocked_slot_dates={date(2026, 7, 5), date(2026, 7, 6)},
    )

    flattened_days = [day for week in weeks for day in week]

    assert "5 • · 3" in flattened_days
    assert "6 •" in flattened_days


def test_shift_month_handles_year_boundaries() -> None:
    assert shift_month(year=2026, month=1, step=-1) == (
        2025,
        12,
    )
    assert shift_month(year=2026, month=12, step=1) == (
        2027,
        1,
    )


def test_format_weekday_name() -> None:
    assert format_weekday_name(6) == "Воскресенье"
