"""
Memory and Agent Investigation Models for RecallOps.
Provides transparent scoring breakdown, explanations, and structured agent outputs.
"""
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from recallops.models.incident import Incident, ActionAttempt


class RelevanceScoreBreakdown(BaseModel):
    service_match_score: float = Field(ge=0.0, le=1.0, description="Service topology match (0 to 1.0)")
    symptom_semantic_score: float = Field(ge=0.0, le=1.0, description="TEMPR / Semantic symptom similarity (0 to 1.0)")
    trigger_match_score: float = Field(ge=0.0, le=1.0, description="Deployment / spike trigger similarity (0 to 1.0)")
    metric_match_score: float = Field(ge=0.0, le=1.0, description="Metric anomaly pattern similarity (0 to 1.0)")
    composite_score: float = Field(ge=0.0, le=1.0, description="Weighted composite relevance score")
    reasons: List[str] = Field(default_factory=list, description="Explicit bullet-point reasons why this is relevant")


class HistoricalIncidentMatch(BaseModel):
    incident: Incident
    relevance: RelevanceScoreBreakdown
    retrieval_method: str = Field(default="Hindsight TEMPR Multi-Strategy")
    key_takeaway: str = Field(description="Condensed executive takeaway from past incident")
    anti_patterns: List[str] = Field(default_factory=list, description="What failed and should NOT be repeated")
    successful_actions: List[str] = Field(default_factory=list, description="What actually resolved it previously")


class InvestigationHypothesis(BaseModel):
    rank: int
    title: str
    description: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    supporting_evidence: List[str]
    citations: List[str] = Field(default_factory=list, description="e.g. ['INC-101', 'INC-104']")


class ActionToAvoid(BaseModel):
    action: str
    historical_incident_id: str
    why_avoid: str
    failure_impact: str


class DiagnosticCheck(BaseModel):
    check_name: str
    command_or_query: str
    target_component: str
    rationale: str
    is_safe_read_only: bool = True


class MitigationProposal(BaseModel):
    mitigation_step: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    historical_precedent: Optional[str] = None
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    requires_human_approval: bool = True


class AgentInvestigationReport(BaseModel):
    incident_id: str
    mode: Literal["WITHOUT_MEMORY", "WITH_HINDSIGHT_MEMORY"]
    generated_at: str
    status_summary: str
    
    # Core reasoning outputs
    hypotheses: List[InvestigationHypothesis]
    actions_to_avoid: List[ActionToAvoid] = Field(default_factory=list)
    next_checks: List[DiagnosticCheck] = Field(default_factory=list)
    proposed_mitigations: List[MitigationProposal] = Field(default_factory=list)
    
    # Evidentiary backing
    historical_matches: List[HistoricalIncidentMatch] = Field(default_factory=list)
    hindsight_reflection_notes: Optional[str] = None
