export type RiskTier = "standard" | "high";
export type RiskDisposition = "allow" | "abstain" | "human_review";
export type ReviewStatus = "pending" | "approved" | "rejected";
export type ReviewDecisionStatus = Exclude<ReviewStatus, "pending">;

export interface HealthResponse {
  status: "healthy";
  service: string;
  version: string;
  environment: string;
}

export interface ProcessingRun {
  id: string;
  document_id: string;
  filename: string;
  parser_name: string;
  parser_version: string;
  chunker_name: string;
  chunker_version: string;
  chunk_count: number;
  embedded_chunk_count: number;
  embedding_provider: string;
  embedding_model: string;
  ready_for_retrieval: boolean;
  created_at: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  processing_run_id: string;
  chunk_count: number;
  created: boolean;
  ready_for_retrieval: boolean;
}

export interface Citation {
  chunk_id: string;
}

export interface GroundedAnswer {
  answer: string;
  citations: Citation[];
  abstained: boolean;
  abstention_reason: string | null;
}

export interface GroundingVerification {
  valid: boolean;
  errors: string[];
}

export interface RiskAssessment {
  disposition: RiskDisposition;
  reason: string;
}

export interface AnswerResponse {
  workflow_id: string;
  processing_run_id: string;
  provider: string;
  model: string;
  retrieved_evidence_count: number;
  final_answer: GroundedAnswer;
  verification: GroundingVerification;
  risk: RiskAssessment;
  review_id: string | null;
}

export interface EvidenceChunk {
  chunk_id: string;
  document_id: string;
  processing_run_id: string;
  content: string;
}

export interface ReviewRecord {
  id: string;
  workflow_id: string;
  status: ReviewStatus;
  reason: string;
  candidate_answer: GroundedAnswer;
  evidence: EvidenceChunk[];
  reviewer_id: string | null;
  reviewer_comment: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface ReviewDecision {
  status: ReviewDecisionStatus;
  reviewer_id: string;
  comment: string;
}
