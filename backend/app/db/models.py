"""ORM models for persistence. Keep API schemas and business rules elsewhere."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """DME employee account persisted for authentication and order ownership."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    __table_args__ = (Index("ix_users_username_lower", func.lower(username), unique=True),)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Order(Base):
    """Durable medical equipment order owned by a single DME employee."""

    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    patient_first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_dob: Mapped[date] = mapped_column(Date, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_npi: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="orders")


class PendingReview(Base):
    """Unvalidated extraction retained separately from orders."""

    __tablename__ = "pending_reviews"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'resolved')", name="valid_status"),
        Index("ix_pending_reviews_user_status", "user_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    extracted: Mapped[dict] = mapped_column(JSON, nullable=False)
    errors: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="pending")
    order_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("orders.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
