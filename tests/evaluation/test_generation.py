from uuid import UUID

from app.evaluation.generation import GenerationEvaluationCase, evaluate_generation
from app.generation.models import Citation, EvidenceChunk, GenerationRequest, GroundedAnswer

RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")
CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000300")


class FakeProvider:
    provider = "fake"
    model = "deterministic"

    async def generate(self, request: GenerationRequest) -> GroundedAnswer:
        return GroundedAnswer(
            answer="Supported.", citations=(Citation(chunk_id=CHUNK_ID),)
        )


async def test_generation_evaluation_reports_measured_rates() -> None:
    case = GenerationEvaluationCase(
        case_id="supported",
        request=GenerationRequest(
            query="Question?",
            processing_run_id=RUN_ID,
            evidence=(
                EvidenceChunk(
                    chunk_id=CHUNK_ID,
                    document_id=DOCUMENT_ID,
                    processing_run_id=RUN_ID,
                    content="Evidence.",
                ),
            ),
        ),
    )
    report = await evaluate_generation(provider=FakeProvider(), cases=(case,))
    assert report.structured_output_rate == 1.0
    assert report.grounding_pass_rate == 1.0
    assert report.abstention_accuracy == 1.0
    assert report.operational_error_rate == 0.0
