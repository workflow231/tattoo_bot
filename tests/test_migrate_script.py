import sqlite3

from scripts.migrate import (
    BUSY_SLOT_REVISION,
    CONFIRMED_SLOT_REVISION,
    INITIAL_REVISION,
    PROCESSED_UPDATES_REVISION,
    WEEKLY_DAY_OFFS_REVISION,
    WORKING_HOURS_REVISION,
    _detect_existing_revision,
    _get_tables,
)


def test_detects_initial_revision_for_legacy_base_schema():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == INITIAL_REVISION
    )


def test_detects_weekly_day_offs_revision():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)
    connection.execute("CREATE TABLE weekly_day_offs (id INTEGER PRIMARY KEY)")

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == WEEKLY_DAY_OFFS_REVISION
    )


def test_detects_confirmed_slot_revision():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)
    connection.execute("""
        CREATE UNIQUE INDEX ux_appointments_confirmed_slot
        ON appointments (appointment_date, appointment_time)
        """)

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == CONFIRMED_SLOT_REVISION
    )


def test_detects_working_hours_revision():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)
    connection.execute("CREATE TABLE weekly_working_hours (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE temporary_working_hours (id INTEGER PRIMARY KEY)")

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == WORKING_HOURS_REVISION
    )


def test_detects_busy_slot_revision():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)
    connection.execute("""
        CREATE UNIQUE INDEX ux_appointments_busy_slot
        ON appointments (appointment_date, appointment_time)
        """)

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == BUSY_SLOT_REVISION
    )


def test_detects_processed_updates_revision():
    connection = sqlite3.connect(":memory:")
    _create_base_tables(connection)
    connection.execute("CREATE TABLE processed_updates (update_id INTEGER PRIMARY KEY)")

    assert (
        _detect_existing_revision(connection, _get_tables(connection))
        == PROCESSED_UPDATES_REVISION
    )


def test_unknown_schema_is_not_stamped():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")

    assert _detect_existing_revision(connection, _get_tables(connection)) is None


def _create_base_tables(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE schedule_exceptions (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE styles (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE sketches (id INTEGER PRIMARY KEY)")
    connection.execute("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            appointment_date DATE,
            appointment_time TIME
        )
        """)
