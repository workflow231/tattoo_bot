import os
import sqlite3
import subprocess
from pathlib import Path

from scripts.migrate import (
    BUSY_SLOT_REVISION,
    CONFIRMED_SLOT_REVISION,
    INITIAL_REVISION,
    PROCESSED_UPDATES_REVISION,
    WEEKLY_DAY_OFFS_REVISION,
    WORKING_HOURS_REVISION,
    _detect_existing_revision,
    _get_tables,
    baseline_legacy_sqlite_connection,
)
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def test_baseline_legacy_sqlite_connection_creates_alembic_version():
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        _create_base_tables(connection.connection.driver_connection)

        baseline_legacy_sqlite_connection(connection)

        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    assert revision == INITIAL_REVISION


def test_alembic_upgrade_handles_existing_legacy_tables(tmp_path):
    db_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(db_path)
    _create_base_tables(connection)
    connection.commit()
    connection.close()

    env = {**os.environ, "DB_PATH": str(db_path)}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )

    connection = sqlite3.connect(db_path)
    tables = _get_tables(connection)
    revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[
        0
    ]
    connection.close()

    assert "processed_updates" in tables
    assert revision == PROCESSED_UPDATES_REVISION


def _create_base_tables(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE schedule_exceptions (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE styles (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    connection.execute("CREATE TABLE sketches (id INTEGER PRIMARY KEY)")
    connection.execute("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            sketch_id INTEGER,
            appointment_date DATE,
            appointment_time TIME,
            status VARCHAR(30),
            reminder_sent BOOLEAN
        )
        """)
