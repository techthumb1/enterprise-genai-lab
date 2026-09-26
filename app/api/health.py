from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.db.session import check_database
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["system"])

SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: SettingsDependency,
) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(
    settings: SettingsDependency,
) -> ReadinessResponse:
    database_ready = await check_database()

    return ReadinessResponse(
        status="ready" if database_ready else "not_ready",
        service=settings.app_name,
        database=database_ready,
    )