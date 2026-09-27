from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import logfire
from fastapi import FastAPI

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
