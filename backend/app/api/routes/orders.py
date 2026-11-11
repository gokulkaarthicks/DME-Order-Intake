"""Authenticated order CRUD endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUserDep, OrderServiceDep
from app.schemas.order import OrderCreate, OrderPublic, OrderUpdate
from app.services.order_service import OrderNotFoundError

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: OrderCreate,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderPublic:
    """Create an order owned by the authenticated DME employee."""
    order = order_service.create(current_user, payload)
    return OrderPublic.model_validate(order)


@router.get("", response_model=list[OrderPublic])
def list_orders(
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> list[OrderPublic]:
    """List orders owned by the authenticated DME employee."""
    orders = order_service.list_for_user(current_user)
    return [OrderPublic.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderPublic)
def get_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderPublic:
    """Retrieve one owned order."""
    try:
        order = order_service.get_for_user(current_user, order_id)
    except OrderNotFoundError as exc:
        raise _not_found() from exc
    return OrderPublic.model_validate(order)


@router.patch("/{order_id}", response_model=OrderPublic)
def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderPublic:
    """Partially update one owned order."""
    try:
        order = order_service.update_for_user(current_user, order_id, payload)
    except OrderNotFoundError as exc:
        raise _not_found() from exc
    return OrderPublic.model_validate(order)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> Response:
    """Delete one owned order."""
    try:
        order_service.delete_for_user(current_user, order_id)
    except OrderNotFoundError as exc:
        raise _not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _not_found() -> HTTPException:
    """Return a non-revealing 404 for missing or inaccessible orders."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Order not found",
    )
