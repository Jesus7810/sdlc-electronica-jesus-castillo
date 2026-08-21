"""add alerts v2 opening evidence

Revision ID: e7a4c6d5f908
Revises: d9f3a8b7c206
Create Date: 2026-08-23 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7a4c6d5f908"
down_revision: str | Sequence[str] | None = "d9f3a8b7c206"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace the temporary alert shape with opening evidence v2."""
    op.drop_index("ix_alerts_reading_id", table_name="alerts")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            postgresql_using="created_at AT TIME ZONE 'UTC'",
        )
        batch_op.alter_column("created_at", new_column_name="opened_at")
        batch_op.alter_column("reading_id", new_column_name="origin_reading_id")
        batch_op.alter_column(
            "reading_value",
            new_column_name="origin_reading_value",
        )
        batch_op.alter_column("threshold", new_column_name="origin_threshold")
        batch_op.add_column(
            sa.Column("condition", sa.String(length=10), nullable=False)
        )
        batch_op.add_column(sa.Column("severity", sa.String(length=10), nullable=False))
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'open'"),
            )
        )
        batch_op.add_column(
            sa.Column("origin_severity", sa.String(length=10), nullable=False)
        )
        batch_op.add_column(sa.Column("last_reading_id", sa.Integer(), nullable=False))
        batch_op.add_column(
            sa.Column("last_reading_value", sa.Float(), nullable=False)
        )
        batch_op.add_column(sa.Column("last_threshold", sa.Float(), nullable=False))
        batch_op.add_column(
            sa.Column("last_severity", sa.String(length=10), nullable=False)
        )
        batch_op.add_column(
            sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=False)
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)
        )
        batch_op.create_foreign_key(
            "fk_alerts_last_reading_id",
            "readings",
            ["last_reading_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_check_constraint(
            "ck_alerts_condition",
            "condition IN ('low', 'high')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_severity",
            "severity IN ('WARNING', 'CRITICAL')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_origin_severity",
            "origin_severity IN ('WARNING', 'CRITICAL')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_last_severity",
            "last_severity IN ('WARNING', 'CRITICAL')",
        )
        batch_op.create_check_constraint("ck_alerts_status_open", "status = 'open'")
    op.create_index(
        "ix_alerts_origin_reading_id",
        "alerts",
        ["origin_reading_id"],
        unique=False,
    )
    op.create_index(
        "ix_alerts_last_reading_id",
        "alerts",
        ["last_reading_id"],
        unique=False,
    )
    where_open = sa.text("status = 'open'")
    op.create_index(
        "uq_alerts_open_sensor_condition",
        "alerts",
        ["sensor_id", "condition"],
        unique=True,
        postgresql_where=where_open,
        sqlite_where=where_open,
    )


def downgrade() -> None:
    """Restore the temporary alert shape for the known-empty database."""
    op.drop_index("uq_alerts_open_sensor_condition", table_name="alerts")
    op.drop_index("ix_alerts_last_reading_id", table_name="alerts")
    op.drop_index("ix_alerts_origin_reading_id", table_name="alerts")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_constraint("ck_alerts_status_open", type_="check")
        batch_op.drop_constraint("ck_alerts_last_severity", type_="check")
        batch_op.drop_constraint("ck_alerts_origin_severity", type_="check")
        batch_op.drop_constraint("ck_alerts_severity", type_="check")
        batch_op.drop_constraint("ck_alerts_condition", type_="check")
        batch_op.drop_constraint("fk_alerts_last_reading_id", type_="foreignkey")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("last_triggered_at")
        batch_op.drop_column("last_severity")
        batch_op.drop_column("last_threshold")
        batch_op.drop_column("last_reading_value")
        batch_op.drop_column("last_reading_id")
        batch_op.drop_column("origin_severity")
        batch_op.drop_column("status")
        batch_op.drop_column("severity")
        batch_op.drop_column("condition")
        batch_op.alter_column(
            "origin_threshold",
            new_column_name="threshold",
        )
        batch_op.alter_column(
            "origin_reading_value",
            new_column_name="reading_value",
        )
        batch_op.alter_column(
            "origin_reading_id",
            new_column_name="reading_id",
        )
        batch_op.alter_column(
            "opened_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            new_column_name="created_at",
            postgresql_using="opened_at AT TIME ZONE 'UTC'",
        )
    op.create_index("ix_alerts_reading_id", "alerts", ["reading_id"], unique=False)
