#!/usr/bin/env python3
"""
Evaluation harness for Brain-AI RAG++ system.

Measures:
- Recall@K (retrieval quality)
- EM/F1 (answer quality)
- Groundedness (% with >= 2 valid citations)
- Hallucination rate
- Refusal rate
- P50/P95 latency
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
LOGGER = logging.getLogger(__name__)


def load_eval_set(path: str) -> List[Dict[str, Any]]:
    """Load evaluation set from JSONL file."""
    examples = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def call_api(url: str, query: str, api_key: str = None) -> Dict[str, Any]:
    """Call the /answer endpoint."""
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    payload = {"query": query}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        LOGGER.error("API call failed for query '%s': %s", query, e)
        return {
            "answer": "API_ERROR",
            "citations": [],
            "confidence": 0.0,
            "error": str(e),
        }


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(text.lower().strip().split())


def exact_match(pred: str, gold: str) -> float:
    """Exact match metric."""
    return 1.0 if normalize_text(pred) == normalize_text(gold) else 0.0


def token_f1(pred: str, gold: str) -> float:
    """Token-level F1 score."""
    pred_tokens = set(normalize_text(pred).split())
    gold_tokens = set(normalize_text(gold).split())
    
    if not gold_tokens:
        return 1.0 if not pred_tokens else 0.0
    
    if not pred_tokens:
        return 0.0
    
    common = pred_tokens & gold_tokens
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def is_grounded(response: Dict[str, Any], min_citations: int = 2) -> bool:
    """Check if answer is grounded with sufficient citations."""
    citations = response.get("citations", [])
    return len(citations) >= min_citations


def is_refusal(answer: str) -> bool:
    """Check if answer is a refusal."""
    normalized = answer.lower().strip()
    refusal_phrases = [
        "insufficient evidence",
        "cannot answer",
        "no relevant context",
        "not enough information",
    ]
    return any(phrase in normalized for phrase in refusal_phrases)


def evaluate(api_url: str, eval_set_path: str, api_key: str = None) -> Dict[str, Any]:
    """Run evaluation on the eval set."""
    examples = load_eval_set(eval_set_path)
    LOGGER.info("Loaded %d examples from %s", len(examples), eval_set_path)
    
    results = []
    latencies = []
    
    for i, example in enumerate(examples, 1):
        query = example["query"]
        expected_answer = example.get("expected_answer", "")
        task_type = example.get("task_type", "factual")
        
        LOGGER.info("[%d/%d] Evaluating: %s", i, len(examples), query[:60])
        
        start = time.time()
        response = call_api(api_url, query, api_key)
        latency = time.time() - start
        latencies.append(latency)
        
        answer = response.get("answer", "")
        confidence = response.get("confidence", 0.0)
        citations = response.get("citations", [])
        
        # Compute metrics
        em = exact_match(answer, expected_answer) if expected_answer else 0.0
        f1 = token_f1(answer, expected_answer) if expected_answer else 0.0
        grounded = is_grounded(response)
        refused = is_refusal(answer)
        
        result = {
            "query": query,
            "expected_answer": expected_answer,
            "predicted_answer": answer,
            "confidence": confidence,
            "citations": citations,
            "task_type": task_type,
            "em": em,
            "f1": f1,
            "grounded": grounded,
            "refused": refused,
            "latency": latency,
        }
        results.append(result)
    
    # Aggregate metrics
    total = len(results)
    
    avg_em = sum(r["em"] for r in results) / total if total > 0 else 0.0
    avg_f1 = sum(r["f1"] for r in results) / total if total > 0 else 0.0
    
    grounded_count = sum(1 for r in results if r["grounded"])
    groundedness = grounded_count / total if total > 0 else 0.0
    
    refusal_count = sum(1 for r in results if r["refused"])
    refusal_rate = refusal_count / total if total > 0 else 0.0
    
    # Hallucination: predicted answer when should refuse (refusal task type)
    refusal_tasks = [r for r in results if r["task_type"] == "refusal"]
    hallucination_count = sum(1 for r in refusal_tasks if not r["refused"])
    hallucination_rate = hallucination_count / len(refusal_tasks) if refusal_tasks else 0.0
    
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    
    summary = {
        "total_examples": total,
        "metrics": {
            "exact_match": avg_em,
            "f1": avg_f1,
            "groundedness": groundedness,
            "refusal_rate": refusal_rate,
            "hallucination_rate": hallucination_rate,
        },
        "latency": {
            "p50_seconds": p50,
            "p95_seconds": p95,
            "p50_ms": int(p50 * 1000),
            "p95_ms": int(p95 * 1000),
        },
        "detailed_results": results,
    }
    
    # Compare against targets
    targets = {
        "recall_at_k": 0.95,
        "groundedness": 0.80,
        "hallucination_max": 0.10,
        "p95_latency_ms": 2000,
    }
    
    passed = []
    failed = []
    
    # Note: We don't have recall@K metric here (would need retrieval-level data)
    # Groundedness check
    if groundedness >= targets["groundedness"]:
        passed.append(f"Groundedness: {groundedness:.3f} >= {targets['groundedness']}")
    else:
        failed.append(f"Groundedness: {groundedness:.3f} < {targets['groundedness']}")
    
    # Hallucination check
    if hallucination_rate <= targets["hallucination_max"]:
        passed.append(f"Hallucination: {hallucination_rate:.3f} <= {targets['hallucination_max']}")
    else:
        failed.append(f"Hallucination: {hallucination_rate:.3f} > {targets['hallucination_max']}")
    
    # Latency check
    if summary["latency"]["p95_ms"] <= targets["p95_latency_ms"]:
        passed.append(f"P95 latency: {summary['latency']['p95_ms']}ms <= {targets['p95_latency_ms']}ms")
    else:
        failed.append(f"P95 latency: {summary['latency']['p95_ms']}ms > {targets['p95_latency_ms']}ms")
    
    summary["targets"] = targets
    summary["passed_checks"] = passed
    summary["failed_checks"] = failed
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Brain-AI RAG++ evaluation")
    parser.add_argument(
        "--api-url",
        default="http://localhost:5001/answer",
        help="API endpoint URL",
    )
    parser.add_argument(
        "--eval-set",
        default="./eval/eval_set.jsonl",
        help="Path to evaluation set JSONL file",
    )
    parser.add_argument(
        "--output",
        default="./eval/metrics.json",
        help="Output path for metrics JSON",
    )
    parser.add_argument(
        "--api-key",
        help="API key for authentication",
    )
    
    args = parser.parse_args()
    
    if not Path(args.eval_set).exists():
        LOGGER.error("Eval set not found: %s", args.eval_set)
        sys.exit(1)
    
    LOGGER.info("Starting evaluation...")
    LOGGER.info("API URL: %s", args.api_url)
    LOGGER.info("Eval set: %s", args.eval_set)
    
    summary = evaluate(args.api_url, args.eval_set, args.api_key)
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    LOGGER.info("Evaluation complete. Results written to %s", output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total examples: {summary['total_examples']}")
    print(f"\nMetrics:")
    for metric, value in summary["metrics"].items():
        print(f"  {metric}: {value:.3f}")
    print(f"\nLatency:")
    print(f"  P50: {summary['latency']['p50_ms']}ms")
    print(f"  P95: {summary['latency']['p95_ms']}ms")
    
    print(f"\nTarget Checks:")
    for check in summary["passed_checks"]:
        print(f"  ✓ {check}")
    for check in summary["failed_checks"]:
        print(f"  ✗ {check}")
    
    if summary["failed_checks"]:
        print("\n⚠ Some targets not met!")
        sys.exit(1)
    else:
        print("\n✅ All targets met!")
        sys.exit(0)


if __name__ == "__main__":
    main()

