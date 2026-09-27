from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.evaluation.generation import GenerationEvaluationCase, evaluate_generation
from app.generation.anthropic_provider import AnthropicGenerationProvider
from app.generation.context import assemble_generation_request
from app.generation.openai_provider import OpenAIGenerationProvider
from app.generation.provider import GenerationProvider
from app.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from app.retrieval.service import RetrievalService
from app.retrieval.sqlalchemy_repository import SQLAlchemyRetrievalRepository

DEFAULT_RUN_ID = UUID("01a0e025-2603-7dbe-a393-0b3b653d7d02")
QUESTIONS = (
    ("homogeneous-graph", "Why is the biomedical graph converted to a homogeneous graph?"),
    ("negative-samples", "How are negative samples generated?"),
    ("unsupported", "Which clinical trial was most successful?"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare structured grounded generation over identical evidence."
    )
    parser.add_argument("--processing-run-id", type=UUID, default=DEFAULT_RUN_ID)
    parser.add_argument("--include-anthropic", action="store_true")
    return parser.parse_args()


async def main(*, processing_run_id: UUID, include_anthropic: bool) -> None:
    settings = get_settings()
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required for retrieval and evaluation")
    openai_key = settings.openai_api_key.get_secret_value()

    async with get_session_factory()() as session:
        retrieval = RetrievalService(
            repository=SQLAlchemyRetrievalRepository(session),
            embedding_provider=OpenAIEmbeddingProvider(
                api_key=openai_key,
                model=settings.openai_embedding_model,
            ),
        )
        cases = []
        for case_id, query in QUESTIONS:
            hits = await retrieval.vector_search(
                processing_run_id=processing_run_id,
                query=query,
                limit=settings.retrieval_top_k,
            )
            cases.append(
                GenerationEvaluationCase(
                    case_id=case_id,
                    request=assemble_generation_request(
                        query=query,
                        processing_run_id=processing_run_id,
                        hits=hits,
                    ),
                    expect_abstention=case_id == "unsupported",
                )
            )

    providers: list[GenerationProvider] = [
        OpenAIGenerationProvider(
            api_key=openai_key,
            model=settings.openai_generation_model,
        )
    ]
    if include_anthropic:
        if settings.anthropic_api_key is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        providers.append(
            AnthropicGenerationProvider(
                api_key=settings.anthropic_api_key.get_secret_value(),
                model="claude-sonnet-4-5",
            )
        )

    for provider in providers:
        report = await evaluate_generation(provider=provider, cases=cases)
        print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(
        main(
            processing_run_id=arguments.processing_run_id,
            include_anthropic=arguments.include_anthropic,
        )
    )
