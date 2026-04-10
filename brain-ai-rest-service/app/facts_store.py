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

# Absolute default: always relative to this file, regardless of cwd.
_DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "facts.db")

# Current schema columns (required)
_REQUIRED_COLUMNS = {"q_hash", "question", "answer", "citations", "confidence", "created_at", "last_accessed"}
# Legacy columns that signal an old schema
_LEGACY_COLUMNS = {"question_hash", "verified_at"}


def _get_columns(conn: sqlite3.Connection, table: str) -> set:
    """Return the set of column names for *table* (empty set if table absent)."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _migrate_schema(conn: sqlite3.Connection, db_path: str) -> None:
    """
    Migrate the *facts* table from any legacy schema to the current schema.

    Migration strategy:
      1. Inspect PRAGMA table_info(facts).
      2. If required columns are missing or legacy columns are present:
         a. Create facts_v2 with the current schema.
         b. Copy rows across, mapping old column names to new ones.
         c. Backfill q_hash from normalized question when missing.
         d. Backfill created_at / last_accessed from legacy timestamps.
         e. Drop old facts and rename facts_v2 → facts.
         f. Recreate indexes.
    """
    present = _get_columns(conn, "facts")
    if not present:
        # Table doesn't exist yet — nothing to migrate.
        return

    missing = _REQUIRED_COLUMNS - present
    legacy = _LEGACY_COLUMNS & present

    if not missing and not legacy:
        # Schema is already current.
        return

    LOGGER.warning(
        "facts table schema mismatch at %s — missing: %s, legacy: %s — running migration",
        db_path,
        missing or "none",
        legacy or "none",
    )

    try:
        conn.execute("""
            CREATE TABLE facts_v2 (
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

        # Build SELECT expression that maps old columns to new ones.
        now = int(time.time())

        # q_hash: use existing q_hash or derive from question
        if "q_hash" in present:
            q_hash_expr = "q_hash"
        else:
            # Will be NULL in the copy; we'll UPDATE afterwards.
            q_hash_expr = "NULL"

        # created_at: prefer existing, fall back to verified_at, then now
        if "created_at" in present:
            created_at_expr = "created_at"
        elif "verified_at" in present:
            created_at_expr = "COALESCE(verified_at, %d)" % now
        else:
            created_at_expr = str(now)

        # last_accessed: prefer existing, fall back to verified_at, then now
        if "last_accessed" in present:
            last_accessed_expr = "last_accessed"
        elif "verified_at" in present:
            last_accessed_expr = "COALESCE(verified_at, %d)" % now
        else:
            last_accessed_expr = str(now)

        # access_count
        access_count_expr = "access_count" if "access_count" in present else "0"

        conn.execute(f"""
            INSERT INTO facts_v2
                (q_hash, question, answer, citations, confidence, created_at, access_count, last_accessed)
            SELECT
                {q_hash_expr},
                question,
                answer,
                citations,
                confidence,
                {created_at_expr},
                {access_count_expr},
                {last_accessed_expr}
            FROM facts
        """)

        # Backfill q_hash where it was NULL (legacy schema had question_hash).
        if "q_hash" not in present:
            if "question_hash" in present:
                # Copy the old hash column directly.
                conn.execute("""
                    UPDATE facts_v2
                    SET q_hash = (
                        SELECT question_hash FROM facts
                        WHERE facts.question = facts_v2.question
                        LIMIT 1
                    )
                    WHERE q_hash IS NULL
                """)
            # Any remaining NULLs: derive from normalized question text.
            rows = conn.execute(
                "SELECT rowid, question FROM facts_v2 WHERE q_hash IS NULL"
            ).fetchall()
            for rowid, question in rows:
                normalized = " ".join(question.lower().strip().split())
                q_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                conn.execute(
                    "UPDATE facts_v2 SET q_hash = ? WHERE rowid = ?",
                    (q_hash, rowid),
                )

        conn.execute("DROP TABLE facts")
        conn.execute("ALTER TABLE facts_v2 RENAME TO facts")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON facts(confidence DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON facts(created_at DESC)")
        conn.commit()

        LOGGER.info("facts table migration completed successfully for %s", db_path)

    except Exception as exc:  # pragma: no cover
        conn.rollback()
        present_after = _get_columns(conn, "facts")
        LOGGER.error(
            "facts table migration FAILED for %s — current columns: %s — error: %s",
            db_path,
            present_after,
            exc,
        )
        raise RuntimeError(
            f"facts store migration failed for {db_path}: {exc}"
        ) from exc


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
    
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        """Initialize facts store with SQLite database."""
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize (and migrate) database
        self._init_db()
        
        LOGGER.info("Facts store initialized at %s", db_path)
    
    def _init_db(self) -> None:
        """Create tables if they don't exist, migrate schema if needed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Run migration first (no-op if schema is current or table absent).
                _migrate_schema(conn, self.db_path)

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
        except Exception as exc:
            LOGGER.error(
                "Facts store initialization failed for %s — %s",
                self.db_path,
                exc,
            )
            raise
    
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
        db_path = os.getenv("FACTS_DB_PATH", _DEFAULT_DB_PATH)
        _facts_store = FactsStore(db_path)
    return _facts_store


__all__ = ["FactsStore", "get_facts_store"]

