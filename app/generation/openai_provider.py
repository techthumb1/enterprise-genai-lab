from __future__ import annotations

from openai import AsyncOpenAI

from app.generation.models import (
    GenerationRequest,
    GroundedAnswer,
)

_SYSTEM_INSTRUCTIONS = """
You are a grounded document-intelligence assistant.

Answer the user's question using only the supplied evidence.

Requirements:
- Do not use outside knowledge.
- Do not invent facts.
- Cite only chunk IDs that appear in the supplied evidence.
- Include every chunk needed to support the answer in citations.
- If the evidence is insufficient, abstain.
- When abstaining, return no answer text and no citations.
- Never invent or transform a chunk ID.
""".strip()


def _format_input(request: GenerationRequest) -> str:
    evidence = "\n\n".join(
        (
            f"<evidence chunk_id=\"{chunk.chunk_id}\" "
            f"document_id=\"{chunk.document_id}\">\n"
            f"{chunk.content}\n"
            "</evidence>"
        )
        for chunk in request.evidence
    )

    return (
        f"<question>\n{request.query}\n</question>\n\n"
        f"<evidence_set>\n{evidence}\n</evidence_set>"
    )


class OpenAIGenerationProvider:
    provider = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
        )

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer:
        response = await self._client.responses.parse(
            model=self.model,
            instructions=_SYSTEM_INSTRUCTIONS,
            input=_format_input(request),
            text_format=GroundedAnswer,
            store=False,
        )

        parsed = response.output_parsed

        if parsed is None:
            raise RuntimeError(
                "OpenAI response did not contain structured output"
            )

        return parsed