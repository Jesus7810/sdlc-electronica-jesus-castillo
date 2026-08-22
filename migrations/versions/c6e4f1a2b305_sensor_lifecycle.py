"""add sensor lifecycle fields

Revision ID: c6e4f1a2b305
Revises: b4c2d9e8f301
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c6e4f1a2b305"
down_revision: str | Sequence[str] | None = "b4c2d9e8f301"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the lifecycle state of a sensor."""
    op.add_column(
        "sensors",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "sensors",
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sensors_is_active", "sensors", ["is_active"], unique=False)


def downgrade() -> None:
    """Remove the lifecycle state of a sensor."""
    op.drop_index("ix_sensors_is_active", table_name="sensors")
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.drop_column("deactivated_at")
        batch_op.drop_column("is_active")
