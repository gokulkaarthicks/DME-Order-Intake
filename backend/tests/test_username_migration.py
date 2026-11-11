"""Exercise the real migration against a separate disposable PostgreSQL database."""
from __future__ import annotations

import os
import subprocess
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.core.security import hash_password, verify_password


def test_username_migration_preserves_users_and_orders() -> None:
    name = f"dme_migration_{uuid4().hex}"
    admin = create_engine("postgresql+psycopg://dme:dme@127.0.0.1:5434/postgres", isolation_level="AUTOCOMMIT")
    url = f"postgresql+psycopg://dme:dme@127.0.0.1:5434/{name}"
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(url)
    env = {**os.environ, "DATABASE_URL": url}
    try:
        subprocess.run([".venv/bin/alembic", "upgrade", "20261111_0001"], env=env, check=True)
        ids = [uuid4() for _ in range(4)]
        emails = ["John.Doe@example.com", "john-doe@example.com", "ab@example.com", "john.doe@other.com"]
        order_id = uuid4()
        password_hash = hash_password("SecurePass123")
        with engine.begin() as conn:
            for user_id, email in zip(ids, emails, strict=True):
                conn.execute(text("INSERT INTO users (id, email, password_hash) VALUES (:id, :email, :hash)"), {"id": user_id, "email": email, "hash": password_hash})
            conn.execute(text("INSERT INTO orders (id, user_id, patient_first_name, patient_last_name, patient_dob, provider_name, provider_npi) VALUES (:id, :user_id, 'Test', 'Patient', '2000-01-01', 'Test Provider', '1234567893')"), {"id": order_id, "user_id": ids[0]})
            before = conn.execute(text("SELECT id, password_hash, created_at FROM users ORDER BY id")).all()
        subprocess.run([".venv/bin/alembic", "upgrade", "head"], env=env, check=True)
        with engine.connect() as conn:
            after = conn.execute(text("SELECT id, password_hash, created_at FROM users ORDER BY id")).all()
            rows = conn.execute(text("SELECT username FROM users ORDER BY id")).scalars().all()
            assert before == after
            assert all(verify_password("SecurePass123", row.password_hash) for row in after)
            assert len(set(rows)) == 4
            assert all(3 <= len(value) <= 32 and value.isascii() and value.replace('_', '').isalnum() for value in rows)
            assert conn.execute(text("SELECT user_id FROM orders WHERE id = :id"), {"id": order_id}).scalar_one() == ids[0]
            assert not conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'email'")).first()
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
