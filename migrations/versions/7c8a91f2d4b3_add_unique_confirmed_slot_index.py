"""add unique confirmed slot index

Revision ID: 7c8a91f2d4b3
Revises: 2f4f7d2f0a11
Create Date: 2026-07-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c8a91f2d4b3"
down_revision: Union[str, Sequence[str], None] = "2f4f7d2f0a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ux_appointments_confirmed_slot",
        "appointments",
        ["appointment_date", "appointment_time"],
        unique=True,
        sqlite_where=sa.text("status = 'confirmed'"),
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ux_appointments_confirmed_slot",
        table_name="appointments",
    )
