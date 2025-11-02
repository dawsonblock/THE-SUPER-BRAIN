"""Canonical facts store for high-confidence answers (triple store)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class FactsStore:
    """
    SQLite-backed store for canonical question-answer pairs.
    
    Only promotes answers that meet quality thresholds:
    - Confidence >= 0.85
    - At least 2 valid citations
    
    Schema:
    - q_hash: Hash of normalized question (PRIMARY KEY)
    - question: Original question text
    - answer: Canonical answer
    - citations: JSON array of citation IDs
    - confidence: Float confidence score
    - created_at: Unix timestamp
    - access_count: Number of times this fact has been retrieved
    - last_accessed: Last access timestamp
    """
    
    def __init__(self, db_path: str = "./data/facts.db"):
        """Initialize facts store with SQLite database."""
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        LOGGER.info("Facts store initialized at %s", db_path)
    
    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    q_hash TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citations TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_confidence ON facts(confidence DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON facts(created_at DESC)
            """)
            conn.commit()
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for consistent hashing."""
        # Lowercase, strip, collapse whitespace
        normalized = " ".join(question.lower().strip().split())
        return normalized
    
    def _hash_question(self, question: str) -> str:
        """Generate hash for question."""
        normalized = self._normalize_question(question)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    def should_promote(
        self,
        confidence: float,
        citations: List[str],
        min_confidence: float = 0.85,
        min_citations: int = 2,
    ) -> bool:
        """
        Check if an answer meets promotion criteria.
        
        Args:
            confidence: Answer confidence score
            citations: List of citation IDs
            min_confidence: Minimum confidence threshold
            min_citations: Minimum number of citations
        
        Returns:
            True if answer should be promoted to facts store
        """
        return confidence >= min_confidence and len(citations) >= min_citations
    
    def upsert(
        self,
        question: str,
        answer: str,
        citations: List[str],
        confidence: float,
    ) -> bool:
        """
        Insert or update a fact in the store.
        
        Args:
            question: Question text
            answer: Answer text
            citations: List of citation IDs
            confidence: Confidence score
        
        Returns:
            True if upserted successfully
        """
        if not self.should_promote(confidence, citations):
            LOGGER.debug("Answer does not meet promotion criteria")
            return False
        
        q_hash = self._hash_question(question)
        now = int(time.time())
        citations_json = json.dumps(citations)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if fact already exists
                existing = conn.execute(
                    "SELECT confidence, access_count FROM facts WHERE q_hash = ?",
                    (q_hash,)
                ).fetchone()
                
                if existing:
                    old_confidence, access_count = existing
                    # Only update if new confidence is higher
                    if confidence > old_confidence:
                        conn.execute("""
                            UPDATE facts
                            SET answer = ?, citations = ?, confidence = ?, last_accessed = ?
                            WHERE q_hash = ?
                        """, (answer, citations_json, confidence, now, q_hash))
                        LOGGER.info("Updated fact for question hash %s (%.3f -> %.3f)",
                                   q_hash[:8], old_confidence, confidence)
                    else:
                        LOGGER.debug("Existing fact has higher confidence, not updating")
                else:
                    # Insert new fact
                    conn.execute("""
                        INSERT INTO facts (q_hash, question, answer, citations, confidence, created_at, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (q_hash, question, answer, citations_json, confidence, now, now))
                    LOGGER.info("Inserted new fact for question hash %s (confidence=%.3f)",
                               q_hash[:8], confidence)
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            LOGGER.error("Failed to upsert fact: %s", e)
            return False
    
    def lookup(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Look up a fact by question.
        
        Args:
            question: Question text
        
        Returns:
            Dict with answer, citations, confidence, or None if not found
        """
        q_hash = self._hash_question(question)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT answer, citations, confidence, access_count
                    FROM facts
                    WHERE q_hash = ?
                """, (q_hash,)).fetchone()
                
                if row:
                    answer, citations_json, confidence, access_count = row
                    
                    # Update access stats
                    now = int(time.time())
                    conn.execute("""
                        UPDATE facts
                        SET access_count = ?, last_accessed = ?
                        WHERE q_hash = ?
                    """, (access_count + 1, now, q_hash))
                    conn.commit()
                    
                    citations = json.loads(citations_json)
                    
                    LOGGER.info("Fact cache hit for question hash %s", q_hash[:8])
                    
                    return {
                        "answer": answer,
                        "citations": citations,
                        "confidence": confidence,
                        "from_cache": True,
                    }
                else:
                    LOGGER.debug("Fact cache miss for question hash %s", q_hash[:8])
                    return None
                    
        except sqlite3.Error as e:
            LOGGER.error("Failed to lookup fact: %s", e)
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the facts store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                avg_confidence = conn.execute("SELECT AVG(confidence) FROM facts").fetchone()[0] or 0.0
                total_accesses = conn.execute("SELECT SUM(access_count) FROM facts").fetchone()[0] or 0
                
                return {
                    "total_facts": total,
                    "avg_confidence": avg_confidence,
                    "total_accesses": total_accesses,
                }
        except sqlite3.Error as e:
            LOGGER.error("Failed to get stats: %s", e)
            return {"error": str(e)}
    
    def list_facts(self, limit: int = 100, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        List facts from the store.
        
        Args:
            limit: Maximum number of facts to return
            min_confidence: Minimum confidence filter
        
        Returns:
            List of fact dicts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute("""
                    SELECT question, answer, citations, confidence, access_count, created_at
                    FROM facts
                    WHERE confidence >= ?
                    ORDER BY confidence DESC, access_count DESC
                    LIMIT ?
                """, (min_confidence, limit)).fetchall()
                
                facts = []
                for row in rows:
                    question, answer, citations_json, confidence, access_count, created_at = row
                    facts.append({
                        "question": question,
                        "answer": answer,
                        "citations": json.loads(citations_json),
                        "confidence": confidence,
                        "access_count": access_count,
                        "created_at": created_at,
                    })
                
                return facts
                
        except sqlite3.Error as e:
            LOGGER.error("Failed to list facts: %s", e)
            return []


# Global instance
_facts_store: Optional[FactsStore] = None


def get_facts_store() -> FactsStore:
    """Get or create global facts store instance."""
    global _facts_store
    if _facts_store is None:
        db_path = os.getenv("FACTS_DB_PATH", "./data/facts.db")
        _facts_store = FactsStore(db_path)
    return _facts_store


__all__ = ["FactsStore", "get_facts_store"]

