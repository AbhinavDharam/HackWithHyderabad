"""
RecallOps SRE Incident Response Agent.
Coordinates Hindsight memory retrieval, multi-signal relevance ranking,
anti-pattern prevention, and evidence-backed investigative reasoning.
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional, Dict, Any
from recallops.models.incident import Incident
from recallops.models.memory_record import (
    AgentInvestigationReport,
    HistoricalIncidentMatch,
    InvestigationHypothesis,
    ActionToAvoid,
    DiagnosticCheck,
    MitigationProposal,
)
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.retrieval.relevance_engine import RelevanceEngine
from recallops.llm.llm_client import LLMClient
from recallops.agent.prompt_templates import (
    SRE_SYSTEM_PROMPT,
    build_cold_start_prompt,
    build_memory_empowered_prompt,
)

logger = logging.getLogger("recallops.agent")


class SREAgent:
    """Intelligent Incident Response Agent backed by Hindsight persistent memory."""

    def __init__(
        self,
        memory_adapter: Optional[HindsightAdapter] = None,
        relevance_engine: Optional[RelevanceEngine] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.memory_adapter = memory_adapter or HindsightAdapter()
        self.relevance_engine = relevance_engine or RelevanceEngine(self.memory_adapter)
        self.llm_client = llm_client or LLMClient()

    def investigate(
        self,
        incident: Incident,
        mode: Literal["WITHOUT_MEMORY", "WITH_HINDSIGHT_MEMORY"] = "WITH_HINDSIGHT_MEMORY",
        historical_pool: Optional[List[Incident]] = None,
    ) -> AgentInvestigationReport:
        """
        Executes investigation loop either in Cold Start mode (no memory)
        or Memory-Empowered mode (using Hindsight).
        """
        now_str = datetime.now(timezone.utc).isoformat()

        if mode == "WITHOUT_MEMORY":
            prompt = build_cold_start_prompt(incident)
            response_text = self.llm_client.generate(prompt=prompt, system_prompt=SRE_SYSTEM_PROMPT)
            parsed_data = self._clean_and_parse_json(response_text)
            
            return AgentInvestigationReport(
                incident_id=incident.incident_id,
                mode="WITHOUT_MEMORY",
                generated_at=now_str,
                status_summary=parsed_data.get("status_summary", "Generic diagnostic triage without organizational memory."),
                hypotheses=[InvestigationHypothesis(**h) for h in parsed_data.get("hypotheses", [])],
                actions_to_avoid=[],
                next_checks=[DiagnosticCheck(**c) for c in parsed_data.get("next_checks", [])],
                proposed_mitigations=[MitigationProposal(**m) for m in parsed_data.get("proposed_mitigations", [])],
                historical_matches=[],
                hindsight_reflection_notes=None,
            )

        # WITH_HINDSIGHT_MEMORY Mode
        candidates = historical_pool or []
        matches = self.relevance_engine.find_relevant_incidents(
            current_incident=incident,
            candidates=candidates,
            threshold=0.40,
            max_matches=3,
        )

        # Reflect over Hindsight memory bank
        query_text = f"Incident on {incident.affected_service}: {' '.join(incident.symptoms[:2])}"
        reflection_notes = self.memory_adapter.reflect(query=query_text)

        prompt = build_memory_empowered_prompt(
            incident=incident,
            matches=matches,
            reflection_notes=reflection_notes,
        )
        response_text = self.llm_client.generate(prompt=prompt, system_prompt=SRE_SYSTEM_PROMPT)
        parsed_data = self._clean_and_parse_json(response_text)

        # Parse and build report
        hypotheses = [InvestigationHypothesis(**h) for h in parsed_data.get("hypotheses", [])]
        actions_to_avoid = [ActionToAvoid(**a) for a in parsed_data.get("actions_to_avoid", [])]
        next_checks = [DiagnosticCheck(**c) for c in parsed_data.get("next_checks", [])]
        proposed_mitigations = [MitigationProposal(**m) for m in parsed_data.get("proposed_mitigations", [])]

        # Ensure historical anti-patterns from matches are prominently included if LLM missed any
        existing_avoid_actions = {a.action.lower() for a in actions_to_avoid}
        for match in matches:
            for fail_act in match.incident.failed_actions():
                if not any(fail_act.action_taken.lower() in existing for existing in existing_avoid_actions):
                    actions_to_avoid.append(
                        ActionToAvoid(
                            action=f"Avoid: {fail_act.action_taken}",
                            historical_incident_id=match.incident.incident_id,
                            why_avoid=fail_act.hypothesis,
                            failure_impact=fail_act.observable_effect,
                        )
                    )

        return AgentInvestigationReport(
            incident_id=incident.incident_id,
            mode="WITH_HINDSIGHT_MEMORY",
            generated_at=now_str,
            status_summary=parsed_data.get("status_summary", "Synthesized analysis utilizing Hindsight persistent memory."),
            hypotheses=hypotheses,
            actions_to_avoid=actions_to_avoid,
            next_checks=next_checks,
            proposed_mitigations=proposed_mitigations,
            historical_matches=matches,
            hindsight_reflection_notes=reflection_notes,
        )

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Cleans markdown JSON code fences and parses into dict."""
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON: {e}. Raw text snippet: {text[:200]}")
            # Fallback to empty structure
            return {
                "status_summary": "Parsing error on agent response. Displaying raw output.",
                "hypotheses": [],
                "actions_to_avoid": [],
                "next_checks": [],
                "proposed_mitigations": [],
            }
