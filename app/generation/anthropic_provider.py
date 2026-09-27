from __future__ import annotations

import json
from typing import Any, cast

from anthropic import AnthropicError, AsyncAnthropic
from pydantic import ValidationError

from app.generation.models import GenerationRequest, GroundedAnswer
from app.generation.provider import GenerationOutputError, GenerationProviderError

_SYSTEM_INSTRUCTIONS = """
You are a grounded document-intelligence assistant.

Answer the user's question using only the supplied evidence. Do not use outside
knowledge. Cite only supplied chunk IDs. If support is insufficient, abstain with
no answer text and no citations. Never invent or transform a chunk ID.
""".strip()


def _format_input(request: GenerationRequest) -> str:
    evidence = "\n\n".join(
        f'<evidence chunk_id="{item.chunk_id}" document_id="{item.document_id}">\n'
        f"{item.content}\n</evidence>"
        for item in request.evidence
    )
    return (
        f"<question>\n{request.query}\n</question>\n\n"
        f"<evidence_set>\n{evidence}\n</evidence_set>"
    )


class AnthropicGenerationProvider:
    provider = "anthropic"

    def __init__(self, *, api_key: str, model: str) -> None:
        self.model = model
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate(self, request: GenerationRequest) -> GroundedAnswer:
        try:
            client = cast(Any, self._client)
            response = await client.messages.create(
                model=self.model,
                max_tokens=1200,
                system=_SYSTEM_INSTRUCTIONS,
                messages=[{"role": "user", "content": _format_input(request)}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": GroundedAnswer.model_json_schema(),
                    }
                },
            )
        except AnthropicError as exc:
            raise GenerationProviderError("generation provider unavailable") from exc

        content = response.content
        if not content or getattr(content[0], "type", None) != "text":
            raise GenerationOutputError("provider returned no structured output")
        try:
            payload = json.loads(content[0].text)
            return GroundedAnswer.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise GenerationOutputError("provider returned invalid structured output") from exc
