"""
Incident Data Models for RecallOps.
Captures full incident lifecycle: context, metrics, attempted actions,
failed vs successful approaches, root cause, and lessons learned.
"""
from enum import Enum
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Severity(str, Enum):
    SEV1 = "SEV-1 (Critical Outage)"
    SEV2 = "SEV-2 (Major Degradation)"
    SEV3 = "SEV-3 (Minor / Degraded)"


class ActionOutcome(str, Enum):
    FAILED = "FAILED"                 # Action worsened the incident or introduced errors
    INEFFECTIVE = "INEFFECTIVE"       # Action had zero or negligible impact
    SUCCESSFUL = "SUCCESSFUL"         # Action resolved or significantly mitigated the issue


class ActionAttempt(BaseModel):
    action_id: str = Field(description="Unique action ID, e.g. ACT-1")
    timestamp: str = Field(description="Time action was executed")
    action_taken: str = Field(description="Detailed command or change made")
    hypothesis: str = Field(description="Why the engineer tested this action")
    outcome: ActionOutcome = Field(description="Outcome: FAILED, INEFFECTIVE, SUCCESSFUL")
    observable_effect: str = Field(description="What happened after executing the action")
    actor: str = Field(default="@oncall-engineer", description="Engineer handle or system")


class IncidentMetric(BaseModel):
    metric_name: str = Field(description="e.g. p99_latency_ms, error_rate_pct, db_connection_utilization")
    observed_value: float = Field(description="Current / Peak observed metric value")
    baseline_value: float = Field(description="Normal expected baseline value")
    unit: str = Field(description="ms, %, count, etc.")


class IncidentTrigger(BaseModel):
    trigger_type: Literal["deployment", "config_change", "traffic_spike", "dependency_outage", "scheduled_job", "infra_failure"]
    description: str = Field(description="Details of what occurred prior to incident")
    timestamp: str = Field(description="When the trigger occurred")


class Incident(BaseModel):
    incident_id: str = Field(description="e.g. INC-101")
    title: str = Field(description="Concise description of the incident")
    affected_service: str = Field(description="Primary service e.g. checkout-service")
    affected_components: List[str] = Field(default_factory=list, description="e.g. ['postgres-pool', 'redis-cache']")
    severity: Severity = Field(default=Severity.SEV2)
    status: Literal["INVESTIGATING", "MITIGATED", "RESOLVED"] = "INVESTIGATING"
    created_at: str
    resolved_at: Optional[str] = None
    
    # Observable symptoms & telemetry
    symptoms: List[str] = Field(default_factory=list, description="Observable errors and symptoms")
    metrics: List[IncidentMetric] = Field(default_factory=list)
    triggers: List[IncidentTrigger] = Field(default_factory=list)
    
    # Human Investigation Path
    investigation_steps: List[str] = Field(default_factory=list)
    actions_attempted: List[ActionAttempt] = Field(default_factory=list)
    
    # Postmortem & Accumulated Wisdom
    root_cause: Optional[str] = None
    final_resolution: Optional[str] = None
    recovery_time_minutes: Optional[int] = None
    lessons_learned: List[str] = Field(default_factory=list)
    runbook_recommendations: List[str] = Field(default_factory=list)

    def failed_actions(self) -> List[ActionAttempt]:
        """Returns all actions that failed or proved counter-productive."""
        return [a for a in self.actions_attempted if a.outcome == ActionOutcome.FAILED]

    def ineffective_actions(self) -> List[ActionAttempt]:
        """Returns all actions that had no impact."""
        return [a for a in self.actions_attempted if a.outcome == ActionOutcome.INEFFECTIVE]

    def successful_actions(self) -> List[ActionAttempt]:
        """Returns all actions that successfully helped resolve the issue."""
        return [a for a in self.actions_attempted if a.outcome == ActionOutcome.SUCCESSFUL]
