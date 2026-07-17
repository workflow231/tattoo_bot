import os
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INITIAL_REVISION = "bdcbded95efc"
WEEKLY_DAY_OFFS_REVISION = "2f4f7d2f0a11"
CONFIRMED_SLOT_REVISION = "7c8a91f2d4b3"
WORKING_HOURS_REVISION = "9a7d2c4e6b10"
BUSY_SLOT_REVISION = "0f6c2d8b9a31"
PROCESSED_UPDATES_REVISION = "4e2b8d7f1c90"


def main() -> None:
    db_path = _get_db_path()

    if db_path.exists():
        _stamp_legacy_sqlite_database(db_path)

    _run_alembic("upgrade", "head")


def _get_db_path() -> Path:
    raw_path = os.getenv("DB_PATH")

    if not raw_path:
        return PROJECT_ROOT / "tattoo_bot.db"

    if raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
        raw_path = raw_path[1:]

    db_path = Path(raw_path)

    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path

    return db_path.resolve()


def _stamp_legacy_sqlite_database(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        tables = _get_tables(connection)

        if "alembic_version" in tables or not tables:
            return

        revision = _detect_existing_revision(connection, tables)

    if revision:
        _run_alembic("stamp", revision)


def _get_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
    return {row[0] for row in rows}


def _get_indexes(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
    return {row[0] for row in rows}


def _detect_existing_revision(
    connection: sqlite3.Connection,
    tables: set[str],
) -> str | None:
    base_tables = {
        "schedule_exceptions",
        "styles",
        "users",
        "sketches",
        "appointments",
    }

    if not base_tables.issubset(tables):
        return None

    indexes = _get_indexes(connection)
    revision = INITIAL_REVISION

    if "weekly_day_offs" in tables:
        revision = WEEKLY_DAY_OFFS_REVISION

    if "ux_appointments_confirmed_slot" in indexes:
        revision = CONFIRMED_SLOT_REVISION

    if {"weekly_working_hours", "temporary_working_hours"}.issubset(tables):
        revision = WORKING_HOURS_REVISION

    if "ux_appointments_busy_slot" in indexes:
        revision = BUSY_SLOT_REVISION

    if "processed_updates" in tables:
        revision = PROCESSED_UPDATES_REVISION

    return revision


def _run_alembic(*args: str) -> None:
    subprocess.run(
        ["alembic", *args],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
