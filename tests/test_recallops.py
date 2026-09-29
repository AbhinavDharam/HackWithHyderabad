"""
Unit & Integration Tests for RecallOps.
Built with standard unittest for zero-dependency test runner execution.
"""
import unittest
import json
import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recallops.models.incident import Incident, ActionAttempt, ActionOutcome, Severity, IncidentMetric, IncidentTrigger
from recallops.memory.memory_formatter import MemoryFormatter
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.retrieval.relevance_engine import RelevanceEngine
from recallops.incidents.incident_manager import IncidentManager
from recallops.agent.sre_agent import SREAgent


class TestRecallOps(unittest.TestCase):

    def setUp(self):
        self.sample_incident = Incident(
            incident_id="TEST-INC-1",
            title="Test Database Pool Lock",
            affected_service="checkout-service",
            affected_components=["postgres-pool"],
            severity=Severity.SEV1,
            status="RESOLVED",
            created_at="2026-09-28T10:00:00Z",
            resolved_at="2026-09-28T10:30:00Z",
            recovery_time_minutes=30,
            symptoms=["504 Gateway Timeout", "p99 latency 4500ms"],
            metrics=[
                IncidentMetric(metric_name="p99_latency_ms", observed_value=4500.0, baseline_value=150.0, unit="ms"),
                IncidentMetric(metric_name="db_connection_utilization_pct", observed_value=98.0, baseline_value=25.0, unit="%"),
            ],
            triggers=[
                IncidentTrigger(trigger_type="deployment", description="Release v2.0 deployed", timestamp="2026-09-28T09:45:00Z")
            ],
            actions_attempted=[
                ActionAttempt(
                    action_id="ACT-1",
                    timestamp="2026-09-28T10:10:00Z",
                    action_taken="Scaled pod count to 10",
                    hypothesis="Distribute CPU load",
                    outcome=ActionOutcome.FAILED,
                    observable_effect="Exhausted DB pool further",
                    actor="@devops"
                ),
                ActionAttempt(
                    action_id="ACT-2",
                    timestamp="2026-09-28T10:20:00Z",
                    action_taken="Killed locking query PID 1234",
                    hypothesis="Release table lock",
                    outcome=ActionOutcome.SUCCESSFUL,
                    observable_effect="Latency dropped to 140ms",
                    actor="@sre"
                )
            ],
            root_cause="Unindexed lock contention query on checkout tables.",
            final_resolution="Killed query and added index.",
            lessons_learned=["Never scale pods during DB pool saturation."],
            runbook_recommendations=["Inspect pg_stat_activity before scaling."]
        )

    def test_memory_formatter_decomposition(self):
        units = MemoryFormatter.decompose_incident(self.sample_incident)
        self.assertEqual(len(units), 4)
        
        postmortem = next(u for u in units if u["metadata"]["type"] == "postmortem")
        self.assertEqual(postmortem["document_id"], "TEST-INC-1-POSTMORTEM")
        self.assertIn("checkout-service", postmortem["content"])

        failed_action = next(u for u in units if u["metadata"].get("outcome") == "FAILED")
        self.assertIn("FAILED", failed_action["content"])
        self.assertIn("Scaled pod count to 10", failed_action["content"])

    def test_hindsight_adapter_retain_recall(self):
        adapter = HindsightAdapter(bank_id="test-vault")
        retained = adapter.retain(
            content="Test memory: pg_stat_activity lock on checkout-service",
            document_id="TEST-MEM-1",
            metadata={"service": "checkout-service", "type": "action_experience"},
            tags=["test", "service:checkout-service"]
        )
        self.assertTrue(retained)

        results = adapter.recall(query="checkout-service lock", max_results=2)
        self.assertGreater(len(results), 0)
        self.assertTrue(any("checkout-service" in r["text"] for r in results))

    def test_multi_signal_relevance_engine(self):
        active_incident = Incident(
            incident_id="TEST-ACTIVE-1",
            title="Active Latency Surge",
            affected_service="checkout-service",
            affected_components=["postgres-pool"],
            severity=Severity.SEV1,
            status="INVESTIGATING",
            created_at="2026-09-28T12:00:00Z",
            symptoms=["504 Gateway Timeout", "p99 latency 5000ms"],
            metrics=[
                IncidentMetric(metric_name="p99_latency_ms", observed_value=5000.0, baseline_value=150.0, unit="ms"),
                IncidentMetric(metric_name="db_connection_utilization_pct", observed_value=95.0, baseline_value=25.0, unit="%"),
            ],
            triggers=[
                IncidentTrigger(trigger_type="deployment", description="Release v2.1 deployed", timestamp="2026-09-28T11:45:00Z")
            ]
        )

        engine = RelevanceEngine()
        score = engine.score_candidate(active_incident, self.sample_incident)
        
        self.assertEqual(score.service_match_score, 1.0)
        self.assertGreaterEqual(score.composite_score, 0.80)
        self.assertGreater(len(score.reasons), 0)
        self.assertTrue(any("checkout-service" in r for r in score.reasons))

    def test_agent_cold_vs_memory_mode(self):
        active_incident = Incident(
            incident_id="TEST-ACTIVE-2",
            title="Active Latency Spike",
            affected_service="checkout-service",
            affected_components=["postgres-pool"],
            severity=Severity.SEV1,
            status="INVESTIGATING",
            created_at="2026-09-28T12:00:00Z",
            symptoms=["504 Gateway Timeout", "high latency"],
            metrics=[
                IncidentMetric(metric_name="p99_latency_ms", observed_value=4800.0, baseline_value=150.0, unit="ms"),
            ],
            triggers=[
                IncidentTrigger(trigger_type="deployment", description="Release v2.2 deployed", timestamp="2026-09-28T11:50:00Z")
            ]
        )

        agent = SREAgent()
        # 1. Cold start mode
        report_cold = agent.investigate(active_incident, mode="WITHOUT_MEMORY", historical_pool=[self.sample_incident])
        self.assertEqual(len(report_cold.historical_matches), 0)
        self.assertEqual(len(report_cold.actions_to_avoid), 0)

        # 2. Memory-empowered mode
        report_mem = agent.investigate(active_incident, mode="WITH_HINDSIGHT_MEMORY", historical_pool=[self.sample_incident])
        self.assertEqual(len(report_mem.historical_matches), 1)
        self.assertEqual(report_mem.historical_matches[0].incident.incident_id, "TEST-INC-1")
        self.assertGreater(len(report_mem.actions_to_avoid), 0)
        self.assertTrue(any("Scaled pod count" in a.action for a in report_mem.actions_to_avoid))


if __name__ == "__main__":
    unittest.main()
