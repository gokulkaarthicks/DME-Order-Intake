"""Replace email authentication with usernames without replacing user rows.

Revision ID: 20261111_0002
Revises: 20261111_0001
"""
from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261111_0002"
down_revision: Union[str, Sequence[str], None] = "20261111_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(32), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, email FROM users ORDER BY id")).all()
    used: set[str] = set()
    for user_id, email in rows:
        prefix = email.split("@", 1)[0].strip().lower()
        base = re.sub(r"[^a-z0-9_]", "_", prefix)[:32].ljust(3, "_")
        username = base
        suffix_number = 2
        while username in used:
            suffix = f"_{suffix_number}"
            username = base[:32 - len(suffix)] + suffix
            suffix_number += 1
        used.add(username)
        connection.execute(sa.text("UPDATE users SET username = :username WHERE id = :id"), {"username": username, "id": user_id})
    op.alter_column("users", "username", existing_type=sa.String(32), nullable=False)
    op.create_index("ix_users_username_lower", "users", [sa.text("lower(username)")], unique=True)
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "email")


def downgrade() -> None:
    raise RuntimeError("Cannot restore original email addresses after username migration; restore a database backup instead.")
