"""Cross-encoder reranking for improved relevance."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)

# Lazy load the model to avoid startup overhead
_model = None
_model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _get_model():
    """Lazy-load cross-encoder model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import CrossEncoder
            LOGGER.info("Loading cross-encoder model: %s", _model_name)
            _model = CrossEncoder(_model_name)
            LOGGER.info("Cross-encoder model loaded successfully")
        except ImportError:
            LOGGER.error("sentence-transformers not installed, reranking disabled")
            _model = None
        except Exception as e:
            LOGGER.error("Failed to load cross-encoder model: %s", e)
            _model = None
    return _model


def cross_encode_rerank(
    query: str,
    ctx: List[Dict[str, Any]],
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Rerank context chunks using cross-encoder for better relevance.
    
    Args:
        query: User query
        ctx: List of context chunks with keys: id (or doc_id), text (or content), score
        top_k: Number of top results to return after reranking
    
    Returns:
        Reranked list of context chunks with updated scores
    """
    if not ctx:
        return []
    
    model = _get_model()
    if model is None:
        LOGGER.warning("Cross-encoder not available, returning original ranking")
        return ctx[:top_k]
    
    start = time.perf_counter()
    
    # Prepare pairs for cross-encoder
    pairs = []
    for chunk in ctx:
        text = chunk.get("text", chunk.get("content", ""))
        pairs.append([query, text])
    
    try:
        # Get cross-encoder scores
        scores = model.predict(pairs)
        
        # Create reranked results
        reranked = []
        for i, chunk in enumerate(ctx):
            reranked_chunk = chunk.copy()
            reranked_chunk["score"] = float(scores[i])
            reranked.append(reranked_chunk)
        
        # Sort by new scores (descending)
        reranked.sort(key=lambda x: x["score"], reverse=True)
        
        duration_ms = int((time.perf_counter() - start) * 1000)
        LOGGER.info(
            "Reranked %d chunks in %dms, returning top %d",
            len(ctx), duration_ms, min(top_k, len(reranked))
        )
        
        return reranked[:top_k]
        
    except Exception as e:
        LOGGER.error("Reranking failed: %s, returning original ranking", e)
        return ctx[:top_k]


def ensure_chunk_format(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize chunk format to have consistent keys: id, text, score.
    
    Args:
        chunks: Raw chunks with potentially varying keys
    
    Returns:
        Normalized chunks with id, text, score keys
    """
    normalized = []
    for chunk in chunks:
        normalized_chunk = {
            "id": chunk.get("id", chunk.get("doc_id", "???")),
            "text": chunk.get("text", chunk.get("content", "")),
            "score": chunk.get("score", 0.0),
        }
        normalized.append(normalized_chunk)
    return normalized


__all__ = ["cross_encode_rerank", "ensure_chunk_format"]

