from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import GovernedAnswerWorkflow
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.generation.openai_provider import OpenAIGenerationProvider
from app.generation.service import GenerationService
from app.governance.review import ReviewService
from app.governance.sqlalchemy_repository import SQLAlchemyReviewRepository
from app.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from app.retrieval.service import RetrievalService
from app.retrieval.sqlalchemy_repository import SQLAlchemyRetrievalRepository

SettingsDependency = Annotated[Settings, Depends(get_settings)]
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


def get_answer_workflow(
    settings: SettingsDependency,
    session: SessionDependency,
) -> GovernedAnswerWorkflow:
    if settings.openai_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="generation provider is not configured",
        )
    api_key = settings.openai_api_key.get_secret_value()
    retrieval = RetrievalService(
        repository=SQLAlchemyRetrievalRepository(session),
        embedding_provider=OpenAIEmbeddingProvider(
            api_key=api_key,
            model=settings.openai_embedding_model,
        ),
    )
    generation = GenerationService(
        provider=OpenAIGenerationProvider(
            api_key=api_key,
            model=settings.openai_generation_model,
        )
    )
    review_service = ReviewService(SQLAlchemyReviewRepository(session))
    return GovernedAnswerWorkflow(
        retrieval=retrieval,
        generation=generation,
        review_service=review_service,
        retrieval_limit=settings.retrieval_top_k,
    )


def get_review_service(session: SessionDependency) -> ReviewService:
    return ReviewService(SQLAlchemyReviewRepository(session))


WorkflowDependency = Annotated[GovernedAnswerWorkflow, Depends(get_answer_workflow)]
ReviewServiceDependency = Annotated[ReviewService, Depends(get_review_service)]
