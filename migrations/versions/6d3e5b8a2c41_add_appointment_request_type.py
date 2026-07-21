"""add appointment request type

Revision ID: 6d3e5b8a2c41
Revises: 4e2b8d7f1c90
Create Date: 2026-07-21 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d3e5b8a2c41"
down_revision: Union[str, Sequence[str], None] = "4e2b8d7f1c90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column(
            "sketch_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "request_type",
                sa.String(length=30),
                nullable=False,
                server_default="catalog_sketch",
            )
        )
        batch_op.add_column(
            sa.Column(
                "client_sketch_photo_file_id",
                sa.String(length=255),
                nullable=True,
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    empty_sketch_appointments = connection.execute(
        sa.text("SELECT COUNT(*) FROM appointments WHERE sketch_id IS NULL")
    ).scalar_one()

    if empty_sketch_appointments:
        raise RuntimeError(
            "Cannot downgrade appointment request types: appointments without "
            "sketch_id exist."
        )

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_column("client_sketch_photo_file_id")
        batch_op.drop_column("request_type")
        batch_op.alter_column(
            "sketch_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
