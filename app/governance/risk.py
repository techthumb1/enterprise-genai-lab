from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.generation.models import GroundedAnswer, GroundingVerification


class RiskTier(StrEnum):
    STANDARD = "standard"
    HIGH = "high"


class RiskDisposition(StrEnum):
    ALLOW = "allow"
    ABSTAIN = "abstain"
    HUMAN_REVIEW = "human_review"


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disposition: RiskDisposition
    reason: str


def assess_risk(
    *,
    has_evidence: bool,
    candidate: GroundedAnswer | None,
    verification: GroundingVerification,
    risk_tier: RiskTier,
) -> RiskAssessment:
    """Route only on explicit, auditable system facts."""
    if not has_evidence:
        return RiskAssessment(
            disposition=RiskDisposition.ABSTAIN,
            reason="no retrieval evidence was available",
        )
    if candidate is None:
        return RiskAssessment(
            disposition=RiskDisposition.ABSTAIN,
            reason="generation did not produce a candidate",
        )
    if not verification.valid:
        return RiskAssessment(
            disposition=RiskDisposition.ABSTAIN,
            reason="grounding verification failed",
        )
    if candidate.abstained:
        return RiskAssessment(
            disposition=RiskDisposition.ABSTAIN,
            reason=candidate.abstention_reason or "provider abstained",
        )
    if risk_tier is RiskTier.HIGH:
        return RiskAssessment(
            disposition=RiskDisposition.HUMAN_REVIEW,
            reason="high-risk workflows require human approval",
        )
    return RiskAssessment(
        disposition=RiskDisposition.ALLOW,
        reason="grounding policy passed",
    )
