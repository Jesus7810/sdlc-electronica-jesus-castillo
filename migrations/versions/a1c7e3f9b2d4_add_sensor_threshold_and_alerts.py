"""add sensor threshold and alerts

Revision ID: a1c7e3f9b2d4
Revises: 93b8da0ac204
Create Date: 2026-08-15 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c7e3f9b2d4"
down_revision: str | Sequence[str] | None = "93b8da0ac204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add thresholds for existing sensors and persist anomaly alerts."""
    # Adding as nullable allows the existing rows to be backfilled before the
    # NOT NULL constraint is introduced.  Batch mode rebuilds the table when
    # required by SQLite and is also supported by PostgreSQL.
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.add_column(sa.Column("threshold", sa.Float(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE sensors
            SET threshold = min_value + 0.8 * (max_value - min_value)
            """
        )
    )

    with op.batch_alter_table("sensors") as batch_op:
        batch_op.alter_column(
            "threshold",
            existing_type=sa.Float(),
            nullable=False,
        )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.String(length=50), nullable=False),
        sa.Column("reading_id", sa.Integer(), nullable=False),
        sa.Column("reading_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sensor_id"],
            ["sensors.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reading_id"],
            ["readings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_sensor_id", "alerts", ["sensor_id"], unique=False)
    op.create_index("ix_alerts_reading_id", "alerts", ["reading_id"], unique=False)


def downgrade() -> None:
    """Remove alerts and the sensor threshold column."""
    op.drop_index("ix_alerts_reading_id", table_name="alerts")
    op.drop_index("ix_alerts_sensor_id", table_name="alerts")
    op.drop_table("alerts")

    with op.batch_alter_table("sensors") as batch_op:
        batch_op.drop_column("threshold")
