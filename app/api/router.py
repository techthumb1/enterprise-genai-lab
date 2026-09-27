from fastapi import APIRouter

from app.api.answer import router as answer_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.processing_runs import router as processing_runs_router
from app.api.reviews import router as reviews_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(answer_router)
api_router.include_router(documents_router)
api_router.include_router(processing_runs_router)
api_router.include_router(reviews_router)
