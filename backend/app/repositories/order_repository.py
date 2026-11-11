"""Database operations for Order records with ownership filtering."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Order


class OrderRepository:
    """Repository responsible exclusively for order persistence queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: UUID,
        patient_first_name: str,
        patient_last_name: str,
        patient_dob: date,
        provider_name: str,
        provider_npi: str,
    ) -> Order:
        """Insert an order owned by the authenticated user and flush defaults."""
        order = Order(
            user_id=user_id,
            patient_first_name=patient_first_name,
            patient_last_name=patient_last_name,
            patient_dob=patient_dob,
            provider_name=provider_name,
            provider_npi=provider_npi,
        )
        self._session.add(order)
        self._session.flush()
        return order

    def list_for_user(self, user_id: UUID) -> list[Order]:
        """Return orders owned by the user, newest first with a stable id sort."""
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
        )
        return list(self._session.scalars(statement))

    def get_for_user(self, order_id: UUID, user_id: UUID) -> Order | None:
        """Return one order only when both order_id and user_id match."""
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
        return self._session.scalar(statement)

    def apply_updates(self, order: Order, updates: dict[str, Any]) -> Order:
        """Apply validated field updates to an already ownership-scoped order."""
        for field_name, value in updates.items():
            setattr(order, field_name, value)
        self._session.flush()
        return order

    def delete(self, order: Order) -> None:
        """Delete an already ownership-scoped order."""
        self._session.delete(order)
        self._session.flush()
