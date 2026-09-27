from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import logfire
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(get_settings())
    yield
    await dispose_engine()


def create_app(*, frontend_directory: Path | None = None) -> FastAPI:
    settings = get_settings()

    configure_logging(settings)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.include_router(api_router)
    @application.exception_handler(SQLAlchemyError)
    async def database_unavailable(_request: Request, _exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database unavailable or schema is outdated. "
                "Check /ready and run uv run alembic upgrade head."
            },
        )

    logfire.instrument_fastapi(application)
    application.frontend(
        "/",
        directory=(
            frontend_directory
            if frontend_directory is not None
            else Path(__file__).resolve().parents[1] / "ui" / "dist"
        ),
        fallback="index.html",
        check_dir=False,
    )

    return application


app = create_app()
