"""
Prompt Templates for RecallOps Incident Response Agent.
Enforces strict citations, anti-pattern separation, and non-autonomous advisory posture.
"""
import json
from typing import List
from recallops.models.incident import Incident
from recallops.models.memory_record import HistoricalIncidentMatch

SRE_SYSTEM_PROMPT = """You are RecallOps, an elite Incident Response and Site Reliability Engineering (SRE) Assistant.
Your core mission is to empower on-call engineers with accumulated organizational memory from past incidents.

OPERATIONAL PRINCIPLES:
1. Advisory Only: Propose diagnostic verification steps and safe mitigations. The human engineer remains in full command.
2. Strict Citations: Whenever making claims derived from past incidents, cite the incident ID explicitly (e.g. [INC-101]).
3. Differentiate Action Outcomes: Crucially distinguish between actions that SUCCEEDED vs actions that FAILED in the past.
4. Highlight Anti-Patterns: Always warn engineers against repeating previously failed actions.
5. Strict JSON Output: You must respond in valid JSON conforming to the requested schema.
"""


def build_cold_start_prompt(incident: Incident) -> str:
    """Prompt for investigating an incident WITHOUT organizational memory."""
    symptoms_str = "\n".join([f"- {s}" for s in incident.symptoms])
    metrics_str = "\n".join([f"- {m.metric_name}: observed={m.observed_value}{m.unit}, baseline={m.baseline_value}{m.unit}" for m in incident.metrics])
    triggers_str = "\n".join([f"- {t.trigger_type}: {t.description}" for t in incident.triggers])

    return f"""INVESTIGATION REQUEST [MODE: WITHOUT_MEMORY / COLD START]

Current Active Incident:
- ID: {incident.incident_id}
- Service: {incident.affected_service}
- Severity: {incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}
- Symptoms:
{symptoms_str}
- Metrics:
{metrics_str}
- Preceding Triggers:
{triggers_str}

Notice: You do NOT have access to any historical organizational incident memory. Provide general first-principles DevOps recommendations.

Respond with a JSON object matching this schema:
{{
  "status_summary": "Concise summary of the situation",
  "hypotheses": [
    {{
      "rank": 1,
      "title": "Hypothesis title",
      "description": "Details",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "supporting_evidence": ["evidence 1"],
      "citations": []
    }}
  ],
  "actions_to_avoid": [],
  "next_checks": [
    {{
      "check_name": "Check title",
      "command_or_query": "CLI or SQL check",
      "target_component": "component name",
      "rationale": "Why check this",
      "is_safe_read_only": true
    }}
  ],
  "proposed_mitigations": [
    {{
      "mitigation_step": "Action step",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "historical_precedent": null,
      "risk_level": "LOW" | "MEDIUM" | "HIGH",
      "requires_human_approval": true
    }}
  ]
}}
"""


def build_memory_empowered_prompt(
    incident: Incident,
    matches: List[HistoricalIncidentMatch],
    reflection_notes: str,
) -> str:
    """Prompt for investigating an incident WITH Hindsight organizational memory."""
    symptoms_str = "\n".join([f"- {s}" for s in incident.symptoms])
    metrics_str = "\n".join([f"- {m.metric_name}: observed={m.observed_value}{m.unit}, baseline={m.baseline_value}{m.unit}" for m in incident.metrics])
    triggers_str = "\n".join([f"- {t.trigger_type}: {t.description}" for t in incident.triggers])

    historical_context_blocks = []
    for m in matches:
        inc = m.incident
        relevance_str = f"Composite Relevance: {int(m.relevance.composite_score * 100)}%\nWhy Relevant:\n" + "\n".join([f"  • {r}" for r in m.relevance.reasons])
        failed_str = "\n".join([f"  ❌ FAILED: {a.action_taken} -> {a.observable_effect}" for a in inc.failed_actions()]) or "  None recorded"
        success_str = "\n".join([f"  ✅ SUCCEEDED: {a.action_taken} -> {a.observable_effect}" for a in inc.successful_actions()]) or "  None recorded"
        lessons_str = "\n".join([f"  💡 {l}" for l in inc.lessons_learned]) or "  None recorded"

        block = f"""--- HISTORICAL INCIDENT: [{inc.incident_id}] {inc.title} ---
Service: {inc.affected_service} | Recovery Time: {inc.recovery_time_minutes or '??'}m
{relevance_str}
Root Cause: {inc.root_cause}
Previous Actions Attempted:
{failed_str}
{success_str}
Lessons Learned:
{lessons_str}
"""
        historical_context_blocks.append(block)

    history_text = "\n\n".join(historical_context_blocks)

    return f"""INVESTIGATION REQUEST [MODE: WITH_HINDSIGHT_MEMORY]

Current Active Incident:
- ID: {incident.incident_id}
- Service: {incident.affected_service}
- Severity: {incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}
- Symptoms:
{symptoms_str}
- Metrics:
{metrics_str}
- Preceding Triggers:
{triggers_str}

=== RELEVANT ORGANIZATIONAL MEMORIES FROM HINDSIGHT ===
{history_text}

=== HINDSIGHT REFLECTION SUMMARY ===
{reflection_notes}

TASK:
Synthesize an evidence-backed investigation report.
1. Explicitly warn against repeating actions that FAILED in past relevant incidents (e.g. actions from {', '.join([m.incident.incident_id for m in matches])}).
2. Provide ranked diagnostic hypotheses citing past incident evidence.
3. Recommend safe, read-only diagnostic checks to verify root cause.
4. Recommend proven mitigations based on past successful resolutions.

Respond with a JSON object matching this schema:
{{
  "status_summary": "Concise summary comparing current incident with historical memory",
  "hypotheses": [
    {{
      "rank": 1,
      "title": "Hypothesis title",
      "description": "Details",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "supporting_evidence": ["evidence citing specific metrics and past incidents"],
      "citations": ["INC-xxx"]
    }}
  ],
  "actions_to_avoid": [
    {{
      "action": "Action to avoid",
      "historical_incident_id": "INC-xxx",
      "why_avoid": "Why this failed previously",
      "failure_impact": "The negative impact it had"
    }}
  ],
  "next_checks": [
    {{
      "check_name": "Check title",
      "command_or_query": "CLI or SQL check",
      "target_component": "component name",
      "rationale": "Why check this (with historical citation)",
      "is_safe_read_only": true
    }}
  ],
  "proposed_mitigations": [
    {{
      "mitigation_step": "Action step",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "historical_precedent": "Citation of past resolution",
      "risk_level": "LOW" | "MEDIUM" | "HIGH",
      "requires_human_approval": true
    }}
  ]
}}
"""
