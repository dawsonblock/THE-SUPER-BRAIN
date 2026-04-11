"""Regression tests for facts DB migration across legacy schemas."""

from __future__ import annotations

import hashlib
import sqlite3
import sys
import time
from pathlib import Path

# Ensure brain-ai-rest-service is on the path when tests run from repo root
_SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from app.facts_store import FactsStore, _get_columns


def _norm_hash(question: str) -> str:
    normalized = " ".join(question.lower().strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Helper: build a legacy DB with the specified schema and rows
# ---------------------------------------------------------------------------

def _make_legacy_db_no_citations(db_path: Path) -> None:
    """Schema: question, answer, question_hash, confidence, verified_at — NO citations."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE facts (
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_hash TEXT,
                confidence REAL NOT NULL,
                verified_at INTEGER
            )
        """)
        now = int(time.time())
        conn.execute(
            "INSERT INTO facts VALUES (?, ?, ?, ?, ?)",
            ("What is Python?", "A programming language.", "abc123", 0.95, now),
        )
        conn.execute(
            "INSERT INTO facts VALUES (?, ?, ?, ?, ?)",
            ("What is the sky color?", "Blue.", "def456", 0.90, now - 100),
        )
        conn.commit()


def _make_legacy_db_with_citations(db_path: Path) -> None:
    """Schema: question, answer, question_hash, confidence, verified_at, citations."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE facts (
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_hash TEXT,
                confidence REAL NOT NULL,
                verified_at INTEGER,
                citations TEXT
            )
        """)
        now = int(time.time())
        conn.execute(
            "INSERT INTO facts VALUES (?, ?, ?, ?, ?, ?)",
            ("What is Java?", "A programming language.", "g1", 0.92, now, '["src1"]'),
        )
        conn.commit()


def _make_transitional_db(db_path: Path) -> None:
    """Transitional schema: q_hash, question, answer, confidence, created_at, last_accessed — NO citations."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE facts (
                q_hash TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at INTEGER,
                last_accessed INTEGER
            )
        """)
        now = int(time.time())
        conn.execute(
            "INSERT INTO facts VALUES (?, ?, ?, ?, ?, ?)",
            (_norm_hash("What is Go?"), "What is Go?", "A compiled language.", 0.93, now, now),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_migration_legacy_no_citations(tmp_path):
    """Regression: old schema without citations must not fail migration."""
    db_path = tmp_path / "facts.db"
    _make_legacy_db_no_citations(db_path)

    # Migration runs inside FactsStore.__init__ → _init_db → _migrate_schema
    store = FactsStore(db_path=str(db_path))

    # After migration the canonical schema should be present
    with sqlite3.connect(str(db_path)) as conn:
        cols = _get_columns(conn, "facts")
    assert "citations" in cols
    assert "q_hash" in cols
    assert "created_at" in cols
    assert "last_accessed" in cols

    # Rows must be preserved
    facts = store.list_facts(limit=10)
    assert len(facts) == 2
    answers = {f["question"] for f in facts}
    assert "What is Python?" in answers
    assert "What is the sky color?" in answers

    # Citations should have been backfilled to "[]"
    for fact in facts:
        assert fact["citations"] == []


def test_migration_legacy_with_citations(tmp_path):
    """Old schema that DOES have citations is migrated without data loss."""
    db_path = tmp_path / "facts.db"
    _make_legacy_db_with_citations(db_path)

    store = FactsStore(db_path=str(db_path))
    facts = store.list_facts(limit=10)
    assert len(facts) == 1
    assert facts[0]["citations"] == ["src1"]


def test_migration_transitional_no_citations(tmp_path):
    """Transitional schema (q_hash present, no citations) migrates cleanly."""
    db_path = tmp_path / "facts.db"
    _make_transitional_db(db_path)

    store = FactsStore(db_path=str(db_path))
    facts = store.list_facts(limit=10)
    assert len(facts) == 1
    assert facts[0]["question"] == "What is Go?"
    assert facts[0]["citations"] == []


def test_migration_already_current(tmp_path):
    """Current schema must not trigger a migration (idempotent)."""
    db_path = tmp_path / "facts.db"

    # Create a store (which creates the canonical schema)
    store1 = FactsStore(db_path=str(db_path))
    store1.upsert(
        question="How does HNSW work?",
        answer="Graph-based ANN search.",
        citations=["paper1", "paper2"],
        confidence=0.90,
    )

    # Re-opening must succeed and data must be intact
    store2 = FactsStore(db_path=str(db_path))
    facts = store2.list_facts()
    assert len(facts) == 1
    assert facts[0]["question"] == "How does HNSW work?"


def test_migration_empty_table(tmp_path):
    """Empty legacy table (no rows, no citations) migrates without error."""
    db_path = tmp_path / "facts.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE facts (
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                question_hash TEXT,
                confidence REAL NOT NULL,
                verified_at INTEGER
            )
        """)
        conn.commit()

    store = FactsStore(db_path=str(db_path))
    assert store.list_facts() == []
