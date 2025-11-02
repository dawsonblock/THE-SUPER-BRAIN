"""DeepSeek API client with retry logic and structured outputs."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .config import settings

LOGGER = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = "You are a grounded assistant. Answer only from provided context."


def _stub_response(prompt: str) -> Dict[str, object]:
    preview = " ".join(prompt.strip().split())[:120]
    heuristic = preview if preview else "No context"
    return {
        "answer": f"Answer: {heuristic} (stubbed)",
        "model": "stub",
        "latency_ms": 1,
    }


def deepseek_chat(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    max_tokens: int = 1024,
    temperature: float = 0.0,
    top_p: float = 1.0,
    max_retries: int = 3,
    timeout: int = 60,
) -> str:
    """
    Call DeepSeek chat completion API with retry logic.
    
    Args:
        messages: List of message dicts with role and content
        model: Model name (deepseek-r1, deepseek-chat, deepseek-v3)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        Response content string
        
    Raises:
        RuntimeError: If all retries fail
    """
    # Check for stub mode
    if os.getenv("LLM_STUB") == "1" or os.getenv("SAFE_MODE") == "1":
        LOGGER.info("LLM stub mode enabled, returning mock response")
        # Extract user message for stub
        user_msg = next((m["content"] for m in messages if m.get("role") == "user"), "")
        stub = _stub_response(user_msg)
        # Return plain string to match actual DeepSeek API response format
        return stub["answer"]
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    
    url = os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    backoff = 1.0
    last_error = None
    
    for attempt in range(max_retries):
        try:
            started = time.time()
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", backoff))
                LOGGER.warning("Rate limited, waiting %.1fs (attempt %d/%d)", retry_after, attempt + 1, max_retries)
                time.sleep(retry_after)
                backoff *= 2
                continue
            
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            duration = time.time() - started
            LOGGER.info("DeepSeek call succeeded: model=%s, duration=%.2fs, tokens=%d",
                       model, duration, data.get("usage", {}).get("total_tokens", 0))
            
            return content
            
        except requests.Timeout as e:
            last_error = e
            LOGGER.warning("DeepSeek timeout (attempt %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(backoff)
            backoff *= 2
            
        except requests.HTTPError as e:
            last_error = e
            LOGGER.error("DeepSeek HTTP error (attempt %d/%d): status=%s, body=%s",
                        attempt + 1, max_retries, e.response.status_code, e.response.text[:200])
            if e.response.status_code >= 500:
                # Retry on 5xx
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                # Don't retry on 4xx
                raise RuntimeError(f"DeepSeek HTTP error: {e}")
                
        except Exception as e:
            last_error = e
            LOGGER.error("DeepSeek request failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(backoff)
            backoff *= 2
    
    raise RuntimeError(f"DeepSeek call failed after {max_retries} retries: {last_error}")


def ask_llm(
    prompt: str,
    system: str = DEFAULT_SYSTEM_PROMPT,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> Dict[str, object]:
    """
    Legacy interface for backward compatibility.
    
    Args:
        prompt: User prompt
        system: System prompt
        model: Optional model override
        temperature: Sampling temperature
    
    Returns:
        Dict with answer, model, latency_ms keys
    """
    if settings.llm_stub or settings.safe_mode:
        return _stub_response(prompt)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        LOGGER.warning("DEEPSEEK_API_KEY missing; using stub response")
        return _stub_response(prompt)

    if model is None:
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    started = time.time()
    try:
        content = deepseek_chat(
            messages=messages,
            model=model,
            max_tokens=2048,
            temperature=temperature,
            timeout=settings.llm_timeout,
        )
        latency = int((time.time() - started) * 1000)
        return {"answer": content, "model": model, "latency_ms": latency}
        
    except Exception as exc:
        LOGGER.error("LLM request failed: %s", exc)
        return {
            "answer": f"LLM failure: {exc}",
            "model": model,
            "latency_ms": int((time.time() - started) * 1000),
            "error": str(exc),
        }


__all__ = ["ask_llm", "deepseek_chat"]
