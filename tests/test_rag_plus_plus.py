#!/usr/bin/env python3
"""
Integration tests for RAG++ v3.0 features.

Tests:
- Multi-agent correction
- Evidence gating
- Reranking
- Facts store
- Prompts module
- Verification tools
"""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain-ai-rest-service'))

from app.prompts import make_messages, enforce_json, apply_evidence_gate
from app.agents import solve_candidates, judge, _score_candidate
from app.verification import safe_calculator, verify_answer
from app.facts_store import FactsStore


class TestPromptsModule:
    """Test prompts.py functionality."""
    
    def test_make_messages(self):
        """Test message construction."""
        ctx = [
            {"id": "d1", "text": "Test content", "score": 0.9},
            {"id": "d2", "text": "More content", "score": 0.8},
        ]
        
        messages = make_messages("Test query?", ctx, tau=0.7)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test query?" in messages[1]["content"]
        assert "0.7" in messages[1]["content"]
        assert "[d1]" in messages[1]["content"]
    
    def test_enforce_json_valid(self):
        """Test JSON enforcement with valid response."""
        text = '{"answer": "Test answer", "citations": ["d1"], "confidence": 0.85}'
        result = enforce_json(text)
        
        assert result["answer"] == "Test answer"
        assert result["citations"] == ["d1"]
        assert result["confidence"] == 0.85
    
    def test_enforce_json_wrapped(self):
        """Test JSON enforcement with markdown wrapping."""
        text = 'Here is the answer:\n```json\n{"answer": "Test", "citations": [], "confidence": 0.5}\n```'
        result = enforce_json(text)
        
        assert result["answer"] == "Test"
        assert result["confidence"] == 0.5
    
    def test_enforce_json_invalid(self):
        """Test JSON enforcement with invalid response."""
        text = "This is not JSON at all"
        result = enforce_json(text)
        
        assert result["answer"] == "Insufficient evidence."
        assert result["confidence"] == 0.0
    
    def test_apply_evidence_gate_pass(self):
        """Test evidence gate with sufficient confidence."""
        response = {
            "answer": "Good answer",
            "citations": ["d1", "d2"],
            "confidence": 0.85,
        }
        
        result = apply_evidence_gate(response, tau=0.7)
        
        assert result["answer"] == "Good answer"
        assert result["confidence"] == 0.85
    
    def test_apply_evidence_gate_fail(self):
        """Test evidence gate with insufficient confidence."""
        response = {
            "answer": "Uncertain answer",
            "citations": [],
            "confidence": 0.5,
        }
        
        result = apply_evidence_gate(response, tau=0.7)
        
        assert result["answer"] == "Insufficient evidence."
        assert result["confidence"] == 0.5


class TestAgentsModule:
    """Test agents.py functionality."""
    
    def test_score_candidate(self):
        """Test candidate scoring function."""
        candidate = {
            "answer": "Test answer",
            "citations": ["d1", "d2", "d3"],
            "confidence": 0.8,
        }
        
        score = _score_candidate(candidate)
        
        # Score = 0.8 * 0.8 + 0.2 * min(3/3, 1.0) = 0.64 + 0.2 = 0.84
        assert abs(score - 0.84) < 0.01
    
    def test_score_candidate_no_citations(self):
        """Test scoring with no citations."""
        candidate = {
            "answer": "Test",
            "citations": [],
            "confidence": 0.9,
        }
        
        score = _score_candidate(candidate)
        
        # Score = 0.8 * 0.9 + 0.2 * 0 = 0.72
        assert abs(score - 0.72) < 0.01
    
    def test_judge_selects_best(self):
        """Test judge selects highest scoring candidate."""
        candidates = [
            {"answer": "Low", "citations": [], "confidence": 0.5},
            {"answer": "Best", "citations": ["d1", "d2"], "confidence": 0.9},
            {"answer": "Medium", "citations": ["d1"], "confidence": 0.7},
        ]
        
        result = judge(candidates, tau=0.5)
        
        assert result["answer"] == "Best"
        assert result["confidence"] == 0.9
    
    def test_judge_refuses_below_threshold(self):
        """Test judge refuses when all below threshold."""
        candidates = [
            {"answer": "Low1", "citations": [], "confidence": 0.3},
            {"answer": "Low2", "citations": [], "confidence": 0.4},
        ]
        
        result = judge(candidates, tau=0.7)
        
        assert result["answer"] == "Insufficient evidence."
    
    def test_judge_empty_candidates(self):
        """Test judge with no candidates."""
        result = judge([], tau=0.7)
        
        assert result["answer"] == "Insufficient evidence."


class TestVerificationModule:
    """Test verification.py functionality."""
    
    def test_calculator_basic_math(self):
        """Test calculator with basic operations."""
        result = safe_calculator("2 + 2")
        assert "result" in result
        assert result["result"] == "4"
    
    def test_calculator_advanced_math(self):
        """Test calculator with math functions."""
        result = safe_calculator("sqrt(16)")
        assert "result" in result
        assert result["result"] == "4.0"
    
    def test_calculator_forbidden_import(self):
        """Test calculator rejects dangerous operations."""
        result = safe_calculator("import os")
        assert "error" in result
        assert "Forbidden" in result["error"]
    
    def test_calculator_syntax_error(self):
        """Test calculator handles syntax errors."""
        result = safe_calculator("2 +")
        assert "error" in result
    
    def test_verify_answer_math(self):
        """Test verification for math tasks."""
        result = verify_answer(
            answer="The answer is 42",
            query="What is 6 * 7?",
            task_type="math"
        )
        
        assert result["verified"] == True
        assert result["task_type"] == "math"
    
    def test_verify_answer_factual(self):
        """Test verification for factual tasks."""
        result = verify_answer(
            answer="Paris is the capital",
            query="What is the capital of France?",
            task_type="factual"
        )
        
        assert result["verified"] == True
        assert result["task_type"] == "factual"


class TestFactsStore:
    """Test facts_store.py functionality."""
    
    def setup_method(self):
        """Create temp facts store for each test."""
        import tempfile
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.store = FactsStore(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up temp database."""
        import os
        os.unlink(self.temp_db.name)
    
    def test_should_promote_high_quality(self):
        """Test promotion criteria for high quality answers."""
        assert self.store.should_promote(0.85, ["d1", "d2"]) == True
    
    def test_should_promote_low_confidence(self):
        """Test rejection of low confidence answers."""
        assert self.store.should_promote(0.7, ["d1", "d2"]) == False
    
    def test_should_promote_few_citations(self):
        """Test rejection of answers with few citations."""
        assert self.store.should_promote(0.9, ["d1"]) == False
    
    def test_upsert_and_lookup(self):
        """Test storing and retrieving facts."""
        # Upsert a fact
        success = self.store.upsert(
            question="What is 2+2?",
            answer="4",
            citations=["d1", "d2"],
            confidence=0.95
        )
        
        assert success == True
        
        # Look it up
        result = self.store.lookup("What is 2+2?")
        
        assert result is not None
        assert result["answer"] == "4"
        assert result["confidence"] == 0.95
        assert len(result["citations"]) == 2
        assert result["from_cache"] == True
    
    def test_lookup_miss(self):
        """Test lookup for non-existent fact."""
        result = self.store.lookup("What is the meaning of life?")
        assert result is None
    
    def test_upsert_updates_better_confidence(self):
        """Test that upsert updates with better confidence."""
        # Insert initial fact
        self.store.upsert("Test?", "Answer1", ["d1", "d2"], 0.85)
        
        # Update with higher confidence
        self.store.upsert("Test?", "Answer2", ["d1", "d2"], 0.95)
        
        result = self.store.lookup("Test?")
        assert result["answer"] == "Answer2"
        assert result["confidence"] == 0.95
    
    def test_upsert_keeps_better_confidence(self):
        """Test that upsert doesn't downgrade confidence."""
        # Insert high confidence
        self.store.upsert("Test?", "Answer1", ["d1", "d2"], 0.95)
        
        # Try to update with lower confidence
        self.store.upsert("Test?", "Answer2", ["d1", "d2"], 0.80)
        
        result = self.store.lookup("Test?")
        # Should keep the first answer with higher confidence
        assert result["answer"] == "Answer1"
        assert result["confidence"] == 0.95
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        self.store.upsert("Q1?", "A1", ["d1", "d2"], 0.85)
        self.store.upsert("Q2?", "A2", ["d1", "d2"], 0.95)
        
        stats = self.store.get_stats()
        
        assert stats["total_facts"] == 2
        assert 0.85 <= stats["avg_confidence"] <= 0.95
    
    def test_list_facts(self):
        """Test listing facts."""
        self.store.upsert("Q1?", "A1", ["d1", "d2"], 0.85)
        self.store.upsert("Q2?", "A2", ["d1", "d2"], 0.95)
        
        facts = self.store.list_facts(limit=10)
        
        assert len(facts) == 2
        # Should be sorted by confidence DESC
        assert facts[0]["confidence"] >= facts[1]["confidence"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

