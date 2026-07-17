"""add unique busy slot index

Revision ID: 0f6c2d8b9a31
Revises: 9a7d2c4e6b10
Create Date: 2026-07-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0f6c2d8b9a31"
down_revision: Union[str, Sequence[str], None] = "9a7d2c4e6b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    duplicate_busy_slots = connection.execute(
        sa.text(
            """
            SELECT appointment_date, appointment_time, COUNT(*) AS count
            FROM appointments
            WHERE status IN ('pending', 'confirmed')
            GROUP BY appointment_date, appointment_time
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    if duplicate_busy_slots:
        raise RuntimeError(
            "Cannot create unique busy slot index: duplicate pending/confirmed "
            "appointment slots exist."
        )

    op.drop_index(
        "ux_appointments_confirmed_slot",
        table_name="appointments",
        if_exists=True,
    )
    op.create_index(
        "ux_appointments_busy_slot",
        "appointments",
        ["appointment_date", "appointment_time"],
        unique=True,
        sqlite_where=sa.text("status IN ('pending', 'confirmed')"),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ux_appointments_busy_slot", table_name="appointments")
    op.create_index(
        "ux_appointments_confirmed_slot",
        "appointments",
        ["appointment_date", "appointment_time"],
        unique=True,
        sqlite_where=sa.text("status = 'confirmed'"),
    )
