"""
Hindsight Memory Adapter for RecallOps.
Interfaces with official Hindsight SDK (vectorize-io/hindsight)
and provides resilient fallback handling for live hackathon demos.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from recallops.config import HINDSIGHT_BASE_URL, HINDSIGHT_API_KEY, HINDSIGHT_BANK_ID, CACHE_DIR

logger = logging.getLogger("recallops.memory")

try:
    from hindsight_client import Hindsight
    HINDSIGHT_AVAILABLE = True
except ImportError:
    HINDSIGHT_AVAILABLE = False


class HindsightAdapter:
    """
    Adapter for Hindsight persistent memory system.
    Supports retain, recall, reflect, and memory bank inspection.
    """

    def __init__(self, bank_id: Optional[str] = None):
        self.bank_id = bank_id or HINDSIGHT_BANK_ID
        self.base_url = HINDSIGHT_BASE_URL
        self.api_key = HINDSIGHT_API_KEY
        self.local_cache_file = CACHE_DIR / f"{self.bank_id}_memory_cache.json"
        
        # In-memory mirror for speed and offline demo resilience
        self._local_memory_bank: List[Dict[str, Any]] = self._load_local_cache()
        
        # Official Hindsight Client
        self.client = None
        if HINDSIGHT_AVAILABLE and self.api_key and self.api_key != "your_hindsight_api_key_here":
            try:
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                logger.info(f"Initialized Hindsight client with base_url={self.base_url}")
            except Exception as e:
                logger.warning(f"Could not connect to live Hindsight service: {e}. Falling back to local cache mode.")

    def _load_local_cache(self) -> List[Dict[str, Any]]:
        """Loads cached memory units from disk."""
        if self.local_cache_file.exists():
            try:
                with open(self.local_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading local cache: {e}")
        return []

    def _save_local_cache(self):
        """Persists memories to local disk cache."""
        try:
            with open(self.local_cache_file, "w", encoding="utf-8") as f:
                json.dump(self._local_memory_bank, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving local cache: {e}")

    def is_cloud_connected(self) -> bool:
        """Returns True if connected to live Hindsight Cloud/Server."""
        return self.client is not None

    def retain(
        self,
        content: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        context: Optional[str] = None,
    ) -> bool:
        """
        Stores structured narrative unit into Hindsight.
        Uses official SDK client.retain() if connected, and persists locally.
        """
        memory_unit = {
            "document_id": document_id,
            "content": content,
            "metadata": metadata or {},
            "tags": tags or [],
            "context": context or "",
        }

        # Update local bank mirror (deduplicate by document_id)
        if document_id:
            self._local_memory_bank = [m for m in self._local_memory_bank if m.get("document_id") != document_id]
        self._local_memory_bank.append(memory_unit)
        self._save_local_cache()

        # Call remote Hindsight if connected
        if self.client:
            try:
                self.client.retain(
                    bank_id=self.bank_id,
                    content=content,
                    document_id=document_id,
                    metadata=metadata,
                    tags=tags,
                    context=context,
                )
                logger.info(f"Successfully retained {document_id} into Hindsight bank {self.bank_id}")
                return True
            except Exception as e:
                logger.warning(f"Remote Hindsight retain failed: {e}. Cached locally.")
                return True

        return True

    def recall(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant memory facts from Hindsight.
        Falls back gracefully to local multi-strategy search if remote is unreachable.
        """
        if self.client:
            try:
                response = self.client.recall(
                    bank_id=self.bank_id,
                    query=query,
                    tags=tags,
                )
                # Parse Hindsight response
                results = []
                if hasattr(response, "results") and response.results:
                    for item in response.results:
                        results.append({
                            "text": getattr(item, "text", str(item)),
                            "document_id": getattr(item, "document_id", None),
                            "metadata": getattr(item, "metadata", {}),
                            "score": getattr(item, "score", 0.85),
                        })
                    return results[:max_results]
            except Exception as e:
                logger.warning(f"Hindsight client recall error: {e}. Using local memory engine.")

        # Local multi-strategy search fallback
        return self._local_recall(query=query, tags=tags, max_results=max_results)

    def _local_recall(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Local fallback implementing lexical + token keyword scoring over memory bank.
        """
        query_words = set(query.lower().replace("/", " ").replace("-", " ").split())
        scored_units = []

        for unit in self._local_memory_bank:
            content = unit.get("content", "").lower()
            unit_tags = [t.lower() for t in unit.get("tags", [])]
            
            # Tag match bonus
            tag_bonus = 0.0
            if tags:
                for t in tags:
                    if t.lower() in unit_tags:
                        tag_bonus += 0.3

            # Keyword overlap
            content_words = set(content.replace("/", " ").replace("-", " ").split())
            intersection = query_words.intersection(content_words)
            if not query_words:
                score = 0.0
            else:
                score = (len(intersection) / len(query_words)) * 0.7 + tag_bonus

            if score > 0.05 or (tags and tag_bonus > 0):
                scored_units.append({
                    "text": unit.get("content", ""),
                    "document_id": unit.get("document_id"),
                    "metadata": unit.get("metadata", {}),
                    "score": min(score, 1.0),
                })

        scored_units.sort(key=lambda x: x["score"], reverse=True)
        return scored_units[:max_results]

    def reflect(self, query: str) -> str:
        """
        Synthesizes higher-order reasoning over the memory bank.
        Uses Hindsight client.reflect() if connected, or local synthesis.
        """
        if self.client:
            try:
                response = self.client.reflect(
                    bank_id=self.bank_id,
                    query=query,
                    budget="low",
                )
                if hasattr(response, "text"):
                    return response.text
                elif hasattr(response, "answer"):
                    return response.answer
                return str(response)
            except Exception as e:
                logger.warning(f"Hindsight client reflect error: {e}. Using local synthesis.")

        # Local reflection synthesis
        relevant_memories = self._local_recall(query=query, max_results=4)
        if not relevant_memories:
            return "No previous organizational memory records found for this query."

        summary_snippets = []
        for mem in relevant_memories:
            doc_id = mem.get("document_id", "Unknown")
            first_line = mem.get("text", "").split("\n")[0]
            summary_snippets.append(f"- [{doc_id}] {first_line}")

        return (
            f"RecallOps Historical Reflection:\n"
            f"Synthesized organizational experience across {len(relevant_memories)} historical memories:\n"
            + "\n".join(summary_snippets)
        )

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the current memory bank."""
        total_units = len(self._local_memory_bank)
        postmortems = sum(1 for m in self._local_memory_bank if m.get("metadata", {}).get("type") == "postmortem")
        action_experiences = sum(1 for m in self._local_memory_bank if m.get("metadata", {}).get("type") == "action_experience")
        lessons = sum(1 for m in self._local_memory_bank if m.get("metadata", {}).get("type") == "lessons_learned")
        
        return {
            "bank_id": self.bank_id,
            "connected_to_hindsight": self.is_cloud_connected(),
            "total_memories": total_units,
            "postmortems": postmortems,
            "action_experiences": action_experiences,
            "lessons_and_antipatterns": lessons,
            "base_url": self.base_url,
        }

    def list_all_memories(self) -> List[Dict[str, Any]]:
        """Returns all memory units in the bank."""
        return list(self._local_memory_bank)
