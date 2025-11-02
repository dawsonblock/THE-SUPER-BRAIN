"""Multi-agent correction with solve-verify-judge architecture."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

from .llm_deepseek import deepseek_chat
from .prompts import enforce_json, make_messages

LOGGER = logging.getLogger(__name__)


def solve_candidates(
    query: str,
    ctx: List[Dict[str, Any]],
    tau: float,
    n: int = 3,
    temps: Tuple[float, ...] = (0.0, 0.3, 0.4),
    model_solve: str = "deepseek-chat",
) -> List[Dict[str, Any]]:
    """
    Generate multiple candidate answers with different temperatures.
    
    This implements the "solve" phase of the multi-agent correction pipeline.
    Each solver attempts to answer the query independently, potentially with
    different reasoning approaches due to temperature variation.
    
    Args:
        query: User question
        ctx: Context chunks from retrieval + reranking
        tau: Evidence threshold
        n: Number of candidates to generate
        temps: Temperature values to cycle through
        model_solve: Model to use for solving (typically deepseek-chat)
    
    Returns:
        List of candidate responses, each with answer, citations, confidence
    """
    candidates = []
    
    for i in range(n):
        temp = temps[i % len(temps)]
        
        try:
            LOGGER.info("Generating candidate %d/%d with temperature=%.2f", i + 1, n, temp)
            
            messages = make_messages(query, ctx, tau)
            raw_response = deepseek_chat(
                messages=messages,
                model=model_solve,
                max_tokens=2048,
                temperature=temp,
                top_p=1.0,
                timeout=int(os.getenv("DS_TIMEOUT", "60")),
            )
            
            # Parse and validate response
            candidate = enforce_json(raw_response)
            candidate["solver_id"] = i
            candidate["temperature"] = temp
            candidates.append(candidate)
            
            LOGGER.info(
                "Candidate %d: confidence=%.3f, citations=%d",
                i + 1, candidate.get("confidence", 0.0), len(candidate.get("citations", []))
            )
            
        except Exception as e:
            LOGGER.error("Failed to generate candidate %d: %s", i + 1, e)
            # Add a failed candidate with minimal confidence
            candidates.append({
                "answer": "Insufficient evidence.",
                "citations": [],
                "confidence": 0.0,
                "solver_id": i,
                "temperature": temp,
                "error": str(e),
            })
    
    return candidates


def _score_candidate(candidate: Dict[str, Any]) -> float:
    """
    Score a candidate answer based on confidence and citation quality.
    
    Scoring formula:
    - 80% weight on confidence
    - 20% weight on citation count (normalized, saturates at 3 citations)
    
    Args:
        candidate: Candidate response dict
    
    Returns:
        Combined score in [0, 1]
    """
    confidence = candidate.get("confidence", 0.0)
    citations = candidate.get("citations", [])
    num_citations = len(citations)
    
    # Normalize citation count (saturate at 3 for diminishing returns)
    citation_score = min(num_citations / 3.0, 1.0)
    
    # Weighted combination
    score = 0.8 * confidence + 0.2 * citation_score
    
    return score


def judge(
    candidates: List[Dict[str, Any]],
    tau: float,
) -> Dict[str, Any]:
    """
    Select best candidate from multi-agent solvers.
    
    The judge evaluates all candidates and selects the one with the highest
    combined score. If the best candidate is below threshold, it returns
    a refusal response.
    
    Args:
        candidates: List of candidate responses from solvers
        tau: Evidence threshold
    
    Returns:
        Best candidate, or refusal if all candidates are below threshold
    """
    if not candidates:
        LOGGER.warning("No candidates to judge, returning refusal")
        return {
            "answer": "Insufficient evidence.",
            "citations": [],
            "confidence": 0.0,
        }
    
    # Score all candidates
    scored = []
    for cand in candidates:
        score = _score_candidate(cand)
        scored.append((score, cand))
    
    # Sort by score (descending)
    scored.sort(key=lambda x: x[0], reverse=True)
    
    best_score, best_candidate = scored[0]
    
    LOGGER.info(
        "Judge selected candidate with score=%.3f (confidence=%.3f, citations=%d)",
        best_score,
        best_candidate.get("confidence", 0.0),
        len(best_candidate.get("citations", [])),
    )
    
    # Apply evidence gate
    if best_candidate.get("confidence", 0.0) < tau:
        LOGGER.info("Best candidate below threshold (%.3f < %.3f), refusing",
                   best_candidate.get("confidence", 0.0), tau)
        return {
            "answer": "Insufficient evidence.",
            "citations": [],
            "confidence": best_candidate.get("confidence", 0.0),
        }
    
    # Check for explicit refusal in answer
    if best_candidate.get("answer", "").startswith("Insufficient evidence"):
        LOGGER.info("Best candidate is a refusal answer")
        return best_candidate
    
    return best_candidate


def multi_agent_query(
    query: str,
    ctx: List[Dict[str, Any]],
    tau: float,
    n_solvers: int = 3,
) -> Dict[str, Any]:
    """
    Complete multi-agent query pipeline: solve -> judge.
    
    Args:
        query: User question
        ctx: Context chunks from retrieval
        tau: Evidence threshold
        n_solvers: Number of solver agents
    
    Returns:
        Final answer with answer, citations, confidence
    """
    # Check if multi-agent is enabled
    if os.getenv("MULTI_AGENT_ENABLED", "true").lower() == "false":
        LOGGER.info("Multi-agent disabled, using single solver")
        n_solvers = 1
    
    # Generate candidates
    candidates = solve_candidates(
        query=query,
        ctx=ctx,
        tau=tau,
        n=n_solvers,
        model_solve=os.getenv("SOLVER_MODEL", "deepseek-chat"),
    )
    
    # Judge and select best
    result = judge(candidates, tau)
    
    return result


__all__ = ["solve_candidates", "judge", "multi_agent_query"]

