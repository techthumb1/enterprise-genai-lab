from __future__ import annotations

from typing import Protocol

from app.generation.models import (
    GenerationRequest,
    GroundedAnswer,
)


class GenerationProviderError(RuntimeError):
    """Operational provider failure, distinct from model abstention."""


class GenerationOutputError(RuntimeError):
    """Provider responded, but the output violated the structured contract."""


class GenerationProvider(Protocol):
    provider: str
    model: str

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer:
        ...
