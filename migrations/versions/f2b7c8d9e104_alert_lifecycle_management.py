"""add alert lifecycle management

Revision ID: f2b7c8d9e104
Revises: e7a4c6d5f908
Create Date: 2026-08-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "f2b7c8d9e104"
down_revision: str | Sequence[str] | None = "e7a4c6d5f908"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add lifecycle timestamps and make acknowledged alerts unresolved."""
    op.drop_index("uq_alerts_open_sensor_condition", table_name="alerts")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_constraint("ck_alerts_status_open", type_="check")
        batch_op.add_column(
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_alerts_status",
            "status IN ('open', 'acknowledged', 'resolved')",
        )
        batch_op.create_check_constraint(
            "ck_alerts_acknowledged_at",
            "status != 'acknowledged' OR acknowledged_at IS NOT NULL",
        )
        batch_op.create_check_constraint(
            "ck_alerts_resolved_at",
            "status != 'resolved' OR resolved_at IS NOT NULL",
        )
        batch_op.create_check_constraint(
            "ck_alerts_unresolved_without_resolved_at",
            "status NOT IN ('open', 'acknowledged') OR resolved_at IS NULL",
        )
    where_unresolved = sa.text("status IN ('open', 'acknowledged')")
    op.create_index(
        "uq_alerts_unresolved_sensor_condition",
        "alerts",
        ["sensor_id", "condition"],
        unique=True,
        postgresql_where=where_unresolved,
        sqlite_where=where_unresolved,
    )
    op.create_index(
        "ix_alerts_opened_at_id_desc",
        "alerts",
        [sa.text("opened_at DESC"), sa.text("id DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Restore the open-only schema only when no lifecycle history exists.

    Acknowledged and resolved alerts cannot be represented by the previous
    revision. Refuse the downgrade instead of silently reinterpreting them.
    """
    if not context.is_offline_mode():
        bind = op.get_bind()
        unsupported_status = bind.execute(
            sa.text("SELECT 1 FROM alerts WHERE status != 'open' LIMIT 1")
        ).first()
        if unsupported_status is not None:
            raise RuntimeError(
                "No se puede degradar: existen alertas acknowledged o resolved"
            )
    op.drop_index("ix_alerts_opened_at_id_desc", table_name="alerts")
    op.drop_index("uq_alerts_unresolved_sensor_condition", table_name="alerts")
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_constraint(
            "ck_alerts_unresolved_without_resolved_at",
            type_="check",
        )
        batch_op.drop_constraint("ck_alerts_resolved_at", type_="check")
        batch_op.drop_constraint("ck_alerts_acknowledged_at", type_="check")
        batch_op.drop_constraint("ck_alerts_status", type_="check")
        batch_op.drop_column("resolved_at")
        batch_op.drop_column("acknowledged_at")
        batch_op.create_check_constraint("ck_alerts_status_open", "status = 'open'")
    where_open = sa.text("status = 'open'")
    op.create_index(
        "uq_alerts_open_sensor_condition",
        "alerts",
        ["sensor_id", "condition"],
        unique=True,
        postgresql_where=where_open,
        sqlite_where=where_open,
    )
