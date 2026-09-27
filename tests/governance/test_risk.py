from uuid import UUID

from app.generation.models import Citation, GroundedAnswer, GroundingVerification
from app.governance.risk import RiskDisposition, RiskTier, assess_risk

CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000001")


def valid_answer() -> GroundedAnswer:
    return GroundedAnswer(
        answer="Supported answer.",
        citations=(Citation(chunk_id=CHUNK_ID),),
    )


def test_standard_verified_answer_is_allowed() -> None:
    result = assess_risk(
        has_evidence=True,
        candidate=valid_answer(),
        verification=GroundingVerification(valid=True),
        risk_tier=RiskTier.STANDARD,
    )
    assert result.disposition is RiskDisposition.ALLOW


def test_high_risk_verified_answer_requires_review() -> None:
    result = assess_risk(
        has_evidence=True,
        candidate=valid_answer(),
        verification=GroundingVerification(valid=True),
        risk_tier=RiskTier.HIGH,
    )
    assert result.disposition is RiskDisposition.HUMAN_REVIEW


def test_failed_verification_abstains_before_risk_tier() -> None:
    result = assess_risk(
        has_evidence=True,
        candidate=valid_answer(),
        verification=GroundingVerification(valid=False, errors=("invalid",)),
        risk_tier=RiskTier.HIGH,
    )
    assert result.disposition is RiskDisposition.ABSTAIN
