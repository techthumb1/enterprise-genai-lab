from __future__ import annotations

from typing import Protocol

from app.generation.models import (
    GenerationRequest,
    GroundedAnswer,
)


class GenerationProvider(Protocol):
    provider: str
    model: str

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer:
        ...