"""FastAPI application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import dispose_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure process-level concerns on startup and release them on shutdown."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "Starting %s (%s)",
        settings.app_name,
        settings.environment,
    )
    try:
        yield
    finally:
        dispose_engine()
        logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    # The production image provides this directory. Development continues to use Vite.
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend_dist"
    if (frontend_dir / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str) -> FileResponse:
            if path == "api" or path.startswith("api/") or path in {
                "health", "docs", "redoc", "openapi.json"
            }:
                raise HTTPException(status_code=404, detail="Not Found")
            candidate = (frontend_dir / path).resolve()
            if candidate.is_relative_to(frontend_dir.resolve()) and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(frontend_dir / "index.html")

    return app


app = create_app()
