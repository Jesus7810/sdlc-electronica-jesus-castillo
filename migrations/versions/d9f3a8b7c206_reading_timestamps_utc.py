"""store reading timestamps in utc-aware columns

Revision ID: d9f3a8b7c206
Revises: c6e4f1a2b305
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9f3a8b7c206"
down_revision: str | Sequence[str] | None = "c6e4f1a2b305"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make persisted reading timestamps timezone-aware."""
    with op.batch_alter_table("readings") as batch_op:
        # PostgreSQL must interpret legacy naive timestamps as UTC, rather than
        # applying the database session timezone while changing the column type.
        batch_op.alter_column(
            "timestamp",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            postgresql_using="timestamp AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Restore the previous timestamp column type."""
    with op.batch_alter_table("readings") as batch_op:
        batch_op.alter_column(
            "timestamp",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
        )
