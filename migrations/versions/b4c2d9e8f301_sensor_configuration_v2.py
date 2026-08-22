"""sensor configuration v2

Revision ID: b4c2d9e8f301
Revises: a1c7e3f9b2d4
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c2d9e8f301"
down_revision: str | Sequence[str] | None = "a1c7e3f9b2d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the legacy single threshold with sensor configuration v2."""
    # The declared database is empty. These columns are intentionally NOT NULL:
    # the migration must not invent operational thresholds for historical rows.
    # Batch mode uses ALTER TABLE in PostgreSQL and table recreation only when
    # SQLite requires it, avoiding disruption to referencing foreign keys.
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.add_column(
            sa.Column("location", sa.String(length=255), nullable=False)
        )
        batch_op.add_column(
            sa.Column("low_critical_threshold", sa.Float(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("low_warning_threshold", sa.Float(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("high_warning_threshold", sa.Float(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("high_critical_threshold", sa.Float(), nullable=False)
        )
        batch_op.drop_column("threshold")
        batch_op.create_check_constraint(
            "ck_sensors_threshold_order",
            "min_value < low_critical_threshold "
            "AND low_critical_threshold < low_warning_threshold "
            "AND low_warning_threshold < high_warning_threshold "
            "AND high_warning_threshold < high_critical_threshold "
            "AND high_critical_threshold < max_value",
        )


def downgrade() -> None:
    """Restore the legacy sensor shape for the known-empty development database."""
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.drop_constraint("ck_sensors_threshold_order", type_="check")
        batch_op.add_column(
            sa.Column(
                "threshold",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch_op.drop_column("high_critical_threshold")
        batch_op.drop_column("high_warning_threshold")
        batch_op.drop_column("low_warning_threshold")
        batch_op.drop_column("low_critical_threshold")
        batch_op.drop_column("location")
