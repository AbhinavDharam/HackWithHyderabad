"""
Incident Manager for RecallOps.
Handles incident persistence, updates, and memory retention workflows.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from recallops.models.incident import Incident, ActionAttempt, ActionOutcome, Severity, IncidentMetric, IncidentTrigger
from recallops.memory.hindsight_adapter import HindsightAdapter
from recallops.memory.memory_formatter import MemoryFormatter
from recallops.config import DATA_DIR

logger = logging.getLogger("recallops.incidents")


class IncidentManager:
    """Manages the lifecycle of active and historical incidents."""

    def __init__(self, data_file: Optional[Path] = None, memory_adapter: Optional[HindsightAdapter] = None):
        self.data_file = data_file or (DATA_DIR / "synthetic_incidents.json")
        self.memory_adapter = memory_adapter or HindsightAdapter()
        self.incidents: List[Incident] = self._load_incidents()

    def _load_incidents(self) -> List[Incident]:
        """Loads incidents from JSON store."""
        if not self.data_file.exists():
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
                return [Incident(**d) for d in raw]
        except Exception as e:
            logger.error(f"Failed to load incidents: {e}")
            return []

    def _save_incidents(self):
        """Persists incidents to JSON store."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump([i.model_dump() for i in self.incidents], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save incidents: {e}")

    def get_all(self) -> List[Incident]:
        """Returns all incidents."""
        return list(self.incidents)

    def get_by_id(self, incident_id: str) -> Optional[Incident]:
        """Retrieves an incident by its ID."""
        for inc in self.incidents:
            if inc.incident_id.lower() == incident_id.lower():
                return inc
        return None

    def get_historical_pool(self) -> List[Incident]:
        """Returns all resolved incidents eligible for historical memory matching."""
        return [i for i in self.incidents if i.status == "RESOLVED"]

    def create_incident(self, incident: Incident) -> Incident:
        """Registers a new incident."""
        # Replace if ID exists, otherwise append
        self.incidents = [i for i in self.incidents if i.incident_id != incident.incident_id]
        self.incidents.append(incident)
        self._save_incidents()
        return incident

    def resolve_and_retain(
        self,
        incident_id: str,
        root_cause: str,
        final_resolution: str,
        recovery_time_minutes: int,
        actions_attempted: List[ActionAttempt],
        lessons_learned: List[str],
        runbook_recommendations: Optional[List[str]] = None,
    ) -> Incident:
        """
        Marks an incident as RESOLVED and commits the entire experience into Hindsight memory.
        """
        incident = self.get_by_id(incident_id)
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found.")

        incident.status = "RESOLVED"
        incident.root_cause = root_cause
        incident.final_resolution = final_resolution
        incident.recovery_time_minutes = recovery_time_minutes
        incident.actions_attempted = actions_attempted
        incident.lessons_learned = lessons_learned
        incident.runbook_recommendations = runbook_recommendations or []

        self._save_incidents()

        # Retain into Hindsight
        memory_units = MemoryFormatter.decompose_incident(incident)
        for unit in memory_units:
            self.memory_adapter.retain(
                content=unit["content"],
                document_id=unit["document_id"],
                metadata=unit["metadata"],
                tags=unit["tags"],
            )

        logger.info(f"Retained incident {incident_id} ({len(memory_units)} units) into Hindsight bank {self.memory_adapter.bank_id}")
        return incident
