"""Prompt engineering and JSON enforcement for RAG++."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a grounded AI assistant that answers questions using ONLY provided evidence.

RULES:
1. Use ONLY the CONTEXT chunks provided below
2. Quote relevant passages and cite chunk IDs in square brackets like [C7]
3. If the evidence score for all chunks is below TAU, or if you cannot answer from context, you MUST output:
   {"answer": "Insufficient evidence.", "citations": [], "confidence": 0.0}
4. Be precise and factual
5. Include confidence score based on evidence quality

OUTPUT FORMAT (strict JSON):
{
  "answer": "Your detailed answer here with citations [C1] [C3]",
  "citations": ["C1", "C3"],
  "confidence": 0.85
}

The confidence must be a float between 0.0 and 1.0.
If confidence < TAU, you MUST refuse with "Insufficient evidence."
"""


def make_messages(query: str, ctx_chunks: List[Dict[str, Any]], tau: float) -> List[Dict[str, str]]:
    """
    Build messages for LLM call with query, context chunks, and evidence threshold.
    
    Args:
        query: User question
        ctx_chunks: List of context chunks with keys: id, text, score
        tau: Evidence threshold (confidence below this triggers refusal)
    
    Returns:
        List of message dicts for chat completion API
    """
    context_lines = []
    for chunk in ctx_chunks:
        chunk_id = chunk.get("id", chunk.get("doc_id", "???"))
        score = chunk.get("score", 0.0)
        text = chunk.get("text", chunk.get("content", ""))
        context_lines.append(f"[{chunk_id}] score={score:.3f}\n{text}")
    
    context_str = "\n---\n".join(context_lines) if context_lines else "No context available."
    
    user_content = f"""QUERY: {query}

TAU (evidence threshold): {tau}

CONTEXT:
{context_str}

Provide your answer in strict JSON format as specified."""
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def enforce_json(text: str) -> Dict[str, Any]:
    """
    Extract and validate JSON from LLM response.
    
    Handles cases where:
    - LLM wraps JSON in markdown code blocks
    - LLM adds explanatory text before/after JSON
    - JSON is malformed or missing required fields
    
    Args:
        text: Raw LLM response text
    
    Returns:
        Dict with keys: answer, citations, confidence
        Returns refusal dict if extraction/validation fails
    """
    refusal_response = {
        "answer": "Insufficient evidence.",
        "citations": [],
        "confidence": 0.0,
    }
    
    # Try to extract JSON from response
    # Pattern 1: Look for JSON object (greedy, multiline)
    match = re.search(r'\{[^{}]*"answer"[^{}]*\}', text, re.DOTALL | re.IGNORECASE)
    if not match:
        # Pattern 2: Look for any JSON object
        match = re.search(r'\{.*?\}', text, re.DOTALL)
    
    if not match:
        LOGGER.warning("No JSON found in LLM response, returning refusal")
        return refusal_response
    
    json_str = match.group(0)
    
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        LOGGER.warning("Failed to parse JSON from LLM: %s", e)
        return refusal_response
    
    # Validate required fields
    if "answer" not in obj or "citations" not in obj:
        LOGGER.warning("Missing required fields in LLM JSON response")
        return refusal_response
    
    # Normalize types
    try:
        answer = str(obj["answer"])
        citations = obj.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        citations = [str(c) for c in citations]
        
        confidence = float(obj.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        return {
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
        }
    except (ValueError, TypeError) as e:
        LOGGER.warning("Type conversion error in LLM response: %s", e)
        return refusal_response


def apply_evidence_gate(response: Dict[str, Any], tau: float) -> Dict[str, Any]:
    """
    Apply evidence gating - refuse if confidence below threshold.
    
    Args:
        response: Parsed LLM response with answer, citations, confidence
        tau: Evidence threshold
    
    Returns:
        Original response if confidence >= tau, else refusal response
    """
    confidence = response.get("confidence", 0.0)
    
    if confidence < tau:
        LOGGER.info("Evidence gate triggered: confidence %.3f < tau %.3f", confidence, tau)
        return {
            "answer": "Insufficient evidence.",
            "citations": [],
            "confidence": confidence,
        }
    
    return response


__all__ = ["make_messages", "enforce_json", "apply_evidence_gate", "SYSTEM_PROMPT"]

