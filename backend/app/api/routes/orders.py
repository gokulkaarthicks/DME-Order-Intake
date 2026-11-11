"""Authenticated order CRUD and PDF upload endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import ValidationError

from app.api.deps import CurrentUserDep, ExtractionServiceDep, OrderServiceDep

from app.schemas.extraction import ExtractedFieldsResponse, OrderUploadResponse
from app.schemas.order import OrderCreate, OrderPublic, OrderUpdate
from app.services.extraction_service import ExtractionFailedError, UploadRejectedError
from app.services.order_service import OrderNotFoundError

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[OrderPublic])
def list_orders(
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> list[OrderPublic]:
    """List orders owned by the authenticated DME employee."""
    orders = order_service.list_for_user(current_user)
    return [OrderPublic.model_validate(order) for order in orders]


@router.post("/upload", response_model=OrderUploadResponse)
async def upload_order_pdf(
    current_user: CurrentUserDep,
    extraction_service: ExtractionServiceDep,
    file: UploadFile = File(...),
    corrections: str | None = Form(None),
    review_token: str | None = Form(None),
) -> OrderUploadResponse:
    """Extract order fields from an uploaded PDF and persist only when valid."""
    if (corrections is None) != (review_token is None):
        raise HTTPException(status_code=400, detail="Corrections and review token are required together")
    corrected = None
    if corrections is not None:
        try:
            corrected = OrderCreate.model_validate_json(corrections)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=[
                {"loc": ["body", *error["loc"]], "msg": error["msg"], "type": error["type"]}
                for error in exc.errors()
            ]) from exc
    file_bytes = await file.read()
    try:
        result = extraction_service.process_upload(
            user=current_user,
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            corrections=corrected,
            review_token=review_token,
        )
    except UploadRejectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ExtractionFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return OrderUploadResponse(
        status=result.status,  # type: ignore[arg-type]
        saved=result.saved,
        order_id=result.order_id,
        order=result.order,
        extracted=ExtractedFieldsResponse(
            patient_first_name=result.extracted.patient_first_name,
            patient_last_name=result.extracted.patient_last_name,
            patient_dob=result.extracted.patient_dob,
            provider_name=result.extracted.provider_name,
            provider_npi=result.extracted.provider_npi,
        ),
        errors=result.errors,
        review_token=result.review_token,
    )


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
