"""Add persistent human review items.

Revision ID: 20261111_0003
Revises: 20261111_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20261111_0003"
down_revision = "20261111_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("extracted", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'resolved')", name=op.f("ck_pending_reviews_valid_status")),
    )
    op.create_index("ix_pending_reviews_user_status", "pending_reviews", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_pending_reviews_user_status", table_name="pending_reviews")
    op.drop_table("pending_reviews")
