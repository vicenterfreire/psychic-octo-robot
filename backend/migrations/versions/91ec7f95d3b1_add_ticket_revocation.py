"""add ticket revocation

Revision ID: 91ec7f95d3b1
Revises: 2db7467132b0
Create Date: 2026-08-11 10:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "91ec7f95d3b1"
down_revision: str | None = "2db7467132b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_tickets_revocation_time",
        "tickets",
        "revoked_at IS NULL OR revoked_at >= issued_at",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tickets_revocation_time", "tickets", type_="check")
    op.drop_column("tickets", "revoked_at")
