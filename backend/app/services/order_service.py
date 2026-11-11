"""Order business logic and transaction orchestration."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Order, PendingReview, User
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderUpdate


class OrderNotFoundError(Exception):
    """Raised when an order is missing or not owned by the authenticated user."""


class ReviewAlreadyUsedError(Exception):
    """Raised when an extraction proof has already been consumed."""


class OrderService:
    """Coordinates order CRUD while enforcing ownership through the repository."""

    def __init__(
        self,
        *,
        session: Session,
        order_repository: OrderRepository,
    ) -> None:
        self._session = session
        self._orders = order_repository

    def create(self, user: User, payload: OrderCreate) -> Order:
        """Persist a new order owned by the authenticated user."""
        try:
            order = self._orders.create(
                user_id=user.id,
                **payload.model_dump(),
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        self._session.refresh(order)
        return order

    def create_from_review(self, user: User, payload: OrderCreate, review_id: UUID) -> Order:
        """Consume a review proof and create its order in one transaction."""
        try:
            result = self._session.execute(insert(PendingReview).values(
                id=review_id, user_id=user.id, extracted={}, errors={}, status="resolved"
            ).on_conflict_do_nothing(index_elements=["id"]).returning(PendingReview.id))
            if result.scalar_one_or_none() is None:
                raise ReviewAlreadyUsedError("Review already saved or resolved")
            order = self._orders.create(user_id=user.id, **payload.model_dump())
            receipt = self._session.get(PendingReview, review_id)
            assert receipt is not None
            receipt.order_id = order.id
            self._session.commit()
            self._session.refresh(order)
            return order
        except Exception:
            self._session.rollback()
            raise

    def list_for_user(self, user: User) -> list[Order]:
        """List orders owned by the authenticated user."""
        return self._orders.list_for_user(user.id)

    def get_for_user(self, user: User, order_id: UUID) -> Order:
        """Retrieve one owned order or raise a non-revealing not-found error."""
        order = self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise OrderNotFoundError("Order not found")
        return order

    def update_for_user(
        self,
        user: User,
        order_id: UUID,
        payload: OrderUpdate,
    ) -> Order:
        """Partially update an owned order using only explicitly provided fields."""
        order = self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise OrderNotFoundError("Order not found")

        updates = payload.model_dump(exclude_unset=True)
        try:
            order = self._orders.apply_updates(order, updates)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        self._session.refresh(order)
        return order

    def delete_for_user(self, user: User, order_id: UUID) -> None:
        """Delete an owned order or raise a non-revealing not-found error."""
        order = self._orders.get_for_user(order_id, user.id)
        if order is None:
            raise OrderNotFoundError("Order not found")

        try:
            self._orders.delete(order)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
