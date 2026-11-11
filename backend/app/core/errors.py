"""Consistent HTTP and validation error responses."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_body(
    *,
    detail: Any,
    error_type: str,
) -> dict[str, Any]:
    return {
        "detail": detail,
        "error_type": error_type,
    }


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Return a consistent JSON body for HTTPException responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(detail=exc.detail, error_type="http_error"),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return field-oriented validation errors without leaking internals."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(detail=exc.errors(), error_type="validation_error"),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe 500 response for unexpected failures."""
    logger.exception("Unhandled application error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            detail="Internal server error",
            error_type="internal_error",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach application-wide exception handlers."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
