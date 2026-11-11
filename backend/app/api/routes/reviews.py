"""Authenticated human review endpoints."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.deps import CurrentUserDep, DbSessionDep, SettingsDep
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderPublic
from app.schemas.review import ReviewPublic, ReviewSaveRequest
from app.services.review_service import InvalidReview, ReviewConflict, ReviewNotFound, ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewPublic, status_code=status.HTTP_201_CREATED)
def save_review(payload: ReviewSaveRequest, user: CurrentUserDep, session: DbSessionDep, settings: SettingsDep) -> ReviewPublic:
    try:
        review = ReviewService(session, settings, OrderRepository(session)).save(user, payload)
    except InvalidReview as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail="Review already resolved") from exc
    return ReviewPublic.model_validate(review)


@router.get("", response_model=list[ReviewPublic])
def list_reviews(user: CurrentUserDep, session: DbSessionDep, settings: SettingsDep) -> list[ReviewPublic]:
    return [ReviewPublic.model_validate(review) for review in ReviewService(session, settings, OrderRepository(session)).list_pending(user)]


@router.post("/{review_id}/resolve", response_model=OrderPublic)
def resolve_review(review_id: UUID, payload: OrderCreate, user: CurrentUserDep,
                   session: DbSessionDep, settings: SettingsDep) -> OrderPublic:
    try:
        return ReviewService(session, settings, OrderRepository(session)).resolve(user, review_id, payload)
    except ReviewNotFound as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail="Review already resolved") from exc
