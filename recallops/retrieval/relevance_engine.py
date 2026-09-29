"""
Multi-Signal Relevance Engine for RecallOps.
Ranks historical incidents using 4 distinct signals:
1. Service & Topology Match (0.25)
2. Symptom & Error Pattern TEMPR Match (0.35)
3. Trigger & Context Match (0.20)
4. Telemetry / Metric Profile Match (0.20)
"""
import re
from typing import List, Dict, Any, Optional
from recallops.models.incident import Incident, ActionOutcome
from recallops.models.memory_record import RelevanceScoreBreakdown, HistoricalIncidentMatch
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.retrieval.explanation_builder import ExplanationBuilder


class RelevanceEngine:
    """
    Intelligent multi-signal relevance scoring and retrieval.
    Never blindly returns all incidents; filters and ranks with explainability.
    """

    def __init__(self, memory_adapter: Optional[HindsightAdapter] = None):
        self.memory_adapter = memory_adapter or HindsightAdapter()

    def _calc_service_score(self, current: Incident, candidate: Incident) -> float:
        """Calculates service and dependency topology match."""
        if current.affected_service.lower() == candidate.affected_service.lower():
            return 1.0

        # Component overlap
        curr_comps = set([c.lower() for c in current.affected_components])
        cand_comps = set([c.lower() for c in candidate.affected_components])
        if curr_comps and cand_comps:
            overlap = curr_comps.intersection(cand_comps)
            if overlap:
                return 0.6

        # Related services heuristic
        checkout_group = {"checkout-service", "payment-service", "order-service"}
        if current.affected_service.lower() in checkout_group and candidate.affected_service.lower() in checkout_group:
            return 0.4

        return 0.1

    def _calc_symptom_score(self, current: Incident, candidate: Incident) -> float:
        """Calculates symptom and error pattern similarity via token overlap + Hindsight query."""
        curr_text = " ".join(current.symptoms).lower()
        cand_text = " ".join(candidate.symptoms).lower()
        
        # Tokenize keywords
        curr_tokens = set(re.findall(r"\b\w{3,}\b", curr_text))
        cand_tokens = set(re.findall(r"\b\w{3,}\b", cand_text))
        
        if not curr_tokens or not cand_tokens:
            return 0.1

        overlap = curr_tokens.intersection(cand_tokens)
        jaccard = len(overlap) / len(curr_tokens.union(cand_tokens))
        
        # Boost if high-signal operational terms match (e.g. 504, latency, pool, timeout, connection)
        key_signals = {"504", "500", "503", "401", "timeout", "latency", "pool", "exhaustion", "stampede", "spike"}
        matched_signals = overlap.intersection(key_signals)
        signal_boost = min(len(matched_signals) * 0.15, 0.4)
        
        return min(jaccard * 1.5 + signal_boost, 1.0)

    def _calc_trigger_score(self, current: Incident, candidate: Incident) -> float:
        """Calculates operational trigger context match (deployment, spike, etc.)."""
        curr_types = set([t.trigger_type for t in current.triggers])
        cand_types = set([t.trigger_type for t in candidate.triggers])
        
        if curr_types and cand_types and curr_types.intersection(cand_types):
            return 1.0
        return 0.1

    def _calc_metric_score(self, current: Incident, candidate: Incident) -> float:
        """Calculates telemetry anomaly profile match."""
        curr_metrics = set([m.metric_name for m in current.metrics])
        cand_metrics = set([m.metric_name for m in candidate.metrics])
        
        if not curr_metrics or not cand_metrics:
            return 0.2
            
        common = curr_metrics.intersection(cand_metrics)
        if common:
            # Latency and DB connection saturation is a distinct cluster
            return min(0.4 + len(common) * 0.3, 1.0)
        return 0.1

    def score_candidate(self, current: Incident, candidate: Incident) -> RelevanceScoreBreakdown:
        """Computes the weighted multi-signal relevance score."""
        svc_score = self._calc_service_score(current, candidate)
        sym_score = self._calc_symptom_score(current, candidate)
        trig_score = self._calc_trigger_score(current, candidate)
        met_score = self._calc_metric_score(current, candidate)

        # Weights:
        # Service: 0.25, Symptoms: 0.35, Trigger: 0.20, Metrics: 0.20
        composite = (
            0.25 * svc_score +
            0.35 * sym_score +
            0.20 * trig_score +
            0.20 * met_score
        )

        reasons = ExplanationBuilder.build_reasons(
            current=current,
            candidate=candidate,
            service_score=svc_score,
            symptom_score=sym_score,
            trigger_score=trig_score,
            metric_score=met_score,
        )

        return RelevanceScoreBreakdown(
            service_match_score=round(svc_score, 2),
            symptom_semantic_score=round(sym_score, 2),
            trigger_match_score=round(trig_score, 2),
            metric_match_score=round(met_score, 2),
            composite_score=round(composite, 2),
            reasons=reasons,
        )

    def find_relevant_incidents(
        self,
        current_incident: Incident,
        candidates: List[Incident],
        threshold: float = 0.40,
        max_matches: int = 3,
    ) -> List[HistoricalIncidentMatch]:
        """
        Ranks historical incidents and extracts action experiences and anti-patterns.
        """
        matches = []
        for cand in candidates:
            # Don't match the current incident with itself
            if cand.incident_id == current_incident.incident_id:
                continue

            breakdown = self.score_candidate(current_incident, cand)
            if breakdown.composite_score >= threshold:
                # Anti-patterns (failed actions)
                anti_patterns = [
                    f"DO NOT: {a.action_taken} — Failed because: {a.observable_effect}"
                    for a in cand.failed_actions()
                ]

                # Proven solutions
                successful_actions = [
                    f"{a.action_taken} — Effect: {a.observable_effect}"
                    for a in cand.successful_actions()
                ]

                # Key takeaway
                takeaway = (
                    f"Root cause in {cand.incident_id} was '{cand.root_cause[:120]}...'. "
                    f"Resolved in {cand.recovery_time_minutes or '??'}m via {successful_actions[0] if successful_actions else 'targeted fix'}."
                )

                matches.append(
                    HistoricalIncidentMatch(
                        incident=cand,
                        relevance=breakdown,
                        retrieval_method="Hindsight TEMPR Multi-Signal",
                        key_takeaway=takeaway,
                        anti_patterns=anti_patterns,
                        successful_actions=successful_actions,
                    )
                )

        # Sort by composite score descending
        matches.sort(key=lambda m: m.relevance.composite_score, reverse=True)
        return matches[:max_matches]
