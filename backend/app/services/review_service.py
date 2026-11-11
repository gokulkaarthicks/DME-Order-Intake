"""Persist and atomically resolve user-owned extraction reviews."""
from uuid import UUID
import jwt
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.db.models import PendingReview, User
from app.integrations.extraction import ExtractedOrderFields
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderPublic
from app.schemas.review import ReviewSaveRequest
from app.services.extraction_service import _validate_extracted_fields, extracted_digest


class ReviewNotFound(Exception):
    pass


class ReviewConflict(Exception):
    pass


class InvalidReview(Exception):
    pass


class ReviewService:
    def __init__(self, session: Session, settings: Settings, orders: OrderRepository) -> None:
        self._session, self._settings, self._orders = session, settings, orders

    def save(self, user: User, payload: ReviewSaveRequest) -> PendingReview:
        fields = payload.extracted.model_dump()
        try:
            claims = jwt.decode(payload.review_token, self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
                options={"require": ["exp", "review_user", "purpose", "review_id", "fields_digest"]})
            review_id = UUID(claims["review_id"])
            if (claims["purpose"] != "order_review" or claims["review_user"] != str(user.id)
                    or claims["fields_digest"] != extracted_digest(fields)):
                raise ValueError("Review proof mismatch")
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError) as exc:
            raise InvalidReview("Invalid or expired review. Upload the PDF again") from exc
        _, errors = _validate_extracted_fields(ExtractedOrderFields(**fields))
        if not errors:
            raise InvalidReview("Only incomplete or invalid extractions can be saved for review")
        try:
            self._session.execute(insert(PendingReview).values(id=review_id, user_id=user.id,
                extracted=fields, errors=errors, status="pending").on_conflict_do_nothing(index_elements=["id"]))
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        review = self._session.scalar(select(PendingReview).where(PendingReview.id == review_id, PendingReview.user_id == user.id))
        if review is None:
            raise InvalidReview("Review unavailable")
        if review.status != "pending":
            raise ReviewConflict()
        return review

    def list_pending(self, user: User) -> list[PendingReview]:
        return list(self._session.scalars(select(PendingReview).where(PendingReview.user_id == user.id,
            PendingReview.status == "pending").order_by(PendingReview.created_at.desc())))

    def resolve(self, user: User, review_id: UUID, payload: OrderCreate) -> OrderPublic:
        try:
            review = self._session.scalar(select(PendingReview).where(PendingReview.id == review_id,
                PendingReview.user_id == user.id).with_for_update())
            if review is None:
                raise ReviewNotFound()
            if review.status != "pending":
                raise ReviewConflict()
            order = self._orders.create(user_id=user.id, **payload.model_dump())
            review.status = "resolved"
            review.order_id = order.id
            self._session.flush()
            result = OrderPublic.model_validate(order)
            self._session.commit()
            return result
        except Exception:
            self._session.rollback()
            raise
