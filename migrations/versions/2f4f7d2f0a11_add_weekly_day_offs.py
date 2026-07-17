"""add weekly day offs

Revision ID: 2f4f7d2f0a11
Revises: bdcbded95efc
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f4f7d2f0a11"
down_revision: Union[str, Sequence[str], None] = "bdcbded95efc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "weekly_day_offs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_weekly_day_offs_weekday"),
        "weekly_day_offs",
        ["weekday"],
        unique=True,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_weekly_day_offs_weekday"), table_name="weekly_day_offs")
    op.drop_table("weekly_day_offs")
