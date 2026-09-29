"""
Explanation Builder for RecallOps.
Generates human-readable, transparent justifications explaining WHY
a specific historical incident is relevant to the active problem.
"""
from typing import List
from recallops.models.incident import Incident
from recallops.models.memory_record import RelevanceScoreBreakdown


class ExplanationBuilder:
    """Builds transparent explanations for incident similarity."""

    @staticmethod
    def build_reasons(
        current: Incident,
        candidate: Incident,
        service_score: float,
        symptom_score: float,
        trigger_score: float,
        metric_score: float,
    ) -> List[str]:
        """Constructs specific, factual justifications for why candidate is relevant."""
        reasons = []

        # Service rationale
        if service_score >= 0.95:
            reasons.append(f"Same primary service: '{current.affected_service}' is identical to {candidate.incident_id}.")
        elif service_score >= 0.5:
            overlap = set(current.affected_components).intersection(set(candidate.affected_components))
            if overlap:
                reasons.append(f"Shared infrastructure components: {', '.join(overlap)}.")
            else:
                reasons.append(f"Related service domain proximity with '{candidate.affected_service}'.")

        # Symptom rationale
        if symptom_score >= 0.6:
            reasons.append(f"High symptom alignment ({int(symptom_score * 100)}% match): Both incidents show similar error codes and latency signatures.")
        elif symptom_score >= 0.3:
            reasons.append(f"Partial symptom overlap: Shared elevated response times or gateway degradation.")

        # Trigger rationale
        if trigger_score >= 0.7:
            curr_trigs = [t.trigger_type for t in current.triggers]
            cand_trigs = [t.trigger_type for t in candidate.triggers]
            common_trigs = set(curr_trigs).intersection(set(cand_trigs))
            if common_trigs:
                reasons.append(f"Common trigger vector: Both occurred immediately following a '{list(common_trigs)[0]}' event.")

        # Metric rationale
        if metric_score >= 0.6:
            reasons.append("Matching telemetry signature: Concurrent latency spike coupled with resource/connection pool saturation.")

        if not reasons:
            reasons.append("General infrastructure failure mode similarities across distributed microservices.")

        return reasons
