"""
Memory Formatter for RecallOps.
Prepares structured incident records into high-signal memory units for Hindsight.
Separates:
1. Postmortem summary
2. Action-outcome experience units (failed vs effective vs successful)
3. Operational anti-patterns and runbook heuristics
"""
from typing import List, Dict, Any
from recallops.models.incident import Incident, ActionOutcome


class MemoryFormatter:
    """Formats Incident data into cognitive memory units for Hindsight retention."""

    @staticmethod
    def format_postmortem(incident: Incident) -> Dict[str, Any]:
        """Creates an executive postmortem memory record."""
        symptoms_str = "; ".join(incident.symptoms)
        triggers_str = "; ".join([f"{t.trigger_type}: {t.description}" for t in incident.triggers])
        metrics_str = "; ".join([
            f"{m.metric_name}={m.observed_value}{m.unit} (baseline {m.baseline_value}{m.unit})"
            for m in incident.metrics
        ])
        
        content = (
            f"INCIDENT POSTMORTEM [{incident.incident_id}]: {incident.title}\n"
            f"Service: {incident.affected_service}\n"
            f"Severity: {incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}\n"
            f"Recovery Time: {incident.recovery_time_minutes or 'Unknown'} minutes\n"
            f"Observed Symptoms: {symptoms_str}\n"
            f"Key Metrics: {metrics_str}\n"
            f"Preceding Triggers: {triggers_str}\n"
            f"Root Cause: {incident.root_cause or 'Under investigation'}\n"
            f"Final Resolution: {incident.final_resolution or 'Pending'}\n"
        )
        
        tags = [
            "postmortem",
            f"service:{incident.affected_service}",
            f"incident:{incident.incident_id}",
        ]
        if incident.affected_components:
            for comp in incident.affected_components:
                tags.append(f"component:{comp}")

        metadata = {
            "incident_id": incident.incident_id,
            "type": "postmortem",
            "service": incident.affected_service,
            "status": incident.status,
            "root_cause_summary": (incident.root_cause[:120] + "...") if incident.root_cause and len(incident.root_cause) > 120 else (incident.root_cause or ""),
        }
        
        return {
            "document_id": f"{incident.incident_id}-POSTMORTEM",
            "content": content,
            "metadata": metadata,
            "tags": tags,
        }

    @staticmethod
    def format_action_experiences(incident: Incident) -> List[Dict[str, Any]]:
        """
        Creates individual action-outcome memory units.
        Crucial for differentiating what engineers tried, what failed, and what worked.
        """
        records = []
        for idx, action in enumerate(incident.actions_attempted):
            outcome_marker = "❌ FAILED / COUNTER-PRODUCTIVE" if action.outcome == ActionOutcome.FAILED else (
                "⚠️ INEFFECTIVE" if action.outcome == ActionOutcome.INEFFECTIVE else "✅ SUCCESSFUL RESOLUTION"
            )
            
            content = (
                f"INCIDENT ACTION EXPERIENCE [{incident.incident_id} - Action {action.action_id}]:\n"
                f"Service: {incident.affected_service}\n"
                f"Action Executed: {action.action_taken}\n"
                f"Hypothesis: {action.hypothesis}\n"
                f"Outcome: {action.outcome.value} ({outcome_marker})\n"
                f"Observable Effect: {action.observable_effect}\n"
                f"Context: Symptoms were {'; '.join(incident.symptoms[:2])}\n"
            )
            
            tags = [
                "action_experience",
                f"outcome:{action.outcome.value.lower()}",
                f"service:{incident.affected_service}",
                f"incident:{incident.incident_id}",
            ]
            
            metadata = {
                "incident_id": incident.incident_id,
                "action_id": action.action_id,
                "type": "action_experience",
                "outcome": action.outcome.value,
                "service": incident.affected_service,
                "action_summary": action.action_taken[:100],
            }
            
            records.append({
                "document_id": f"{incident.incident_id}-ACTION-{idx+1}",
                "content": content,
                "metadata": metadata,
                "tags": tags,
            })
            
        return records

    @staticmethod
    def format_lessons_and_antipatterns(incident: Incident) -> List[Dict[str, Any]]:
        """Extracts operational rules and anti-patterns learned from the incident."""
        records = []
        if not incident.lessons_learned:
            return records
            
        lessons_text = "\n".join([f"- {lesson}" for lesson in incident.lessons_learned])
        content = (
            f"OPERATIONAL LESSONS & ANTI-PATTERNS [{incident.incident_id}]:\n"
            f"Service: {incident.affected_service}\n"
            f"Lessons Learned:\n{lessons_text}\n"
        )
        if incident.runbook_recommendations:
            runbooks_text = "\n".join([f"- {rb}" for rb in incident.runbook_recommendations])
            content += f"Runbook Best Practices:\n{runbooks_text}\n"

        tags = [
            "lessons_learned",
            "anti_pattern",
            f"service:{incident.affected_service}",
            f"incident:{incident.incident_id}",
        ]
        
        metadata = {
            "incident_id": incident.incident_id,
            "type": "lessons_learned",
            "service": incident.affected_service,
        }
        
        records.append({
            "document_id": f"{incident.incident_id}-LESSONS",
            "content": content,
            "metadata": metadata,
            "tags": tags,
        })
        
        return records

    @classmethod
    def decompose_incident(cls, incident: Incident) -> List[Dict[str, Any]]:
        """Decomposes an entire incident into all its memory units."""
        units = []
        units.append(cls.format_postmortem(incident))
        units.extend(cls.format_action_experiences(incident))
        units.extend(cls.format_lessons_and_antipatterns(incident))
        return units
