from __future__ import annotations

import json
import os
import re
import requests
from .prompts import ACTOR_REACT_SYSTEM, ACTOR_REFLEXION_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .utils import normalize_answer

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "")


def _resolve_model() -> str:
    """Auto-detect qwen3 model from Ollama if MODEL env not set."""
    global MODEL
    if MODEL:
        return MODEL
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        # Prefer qwen3 8b > 4b > any qwen (also match qwen3.5 naming)
        for preferred in [
            "qwen3:8b", "qwen3.5:9b", "qwen3:4b", "qwen3.5:4b",
            "qwen3:latest", "qwen3.5:latest", "qwen2.5:7b",
        ]:
            for m in models:
                if preferred in m:
                    MODEL = m
                    return MODEL
        # Fallback to any qwen model
        for m in models:
            if "qwen" in m.lower():
                MODEL = m
                return MODEL
        # Last resort: first model
        if models:
            MODEL = models[0]
            return MODEL
    except Exception as e:
        print(f"[Ollama] Could not list models: {e}")
    MODEL = "qwen3.5:4b"
    return MODEL


def _call_ollama(system: str, user: str, temperature: float = 0.1) -> tuple[str, int]:
    """Call Ollama API and return (response_text, token_count)."""
    model = _resolve_model()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "keep_alive": "30m",  # Keep model loaded for 30 min
        "options": {"temperature": temperature, "num_predict": 768},
    }
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        text = data["message"].get("content", "").strip()
        thinking = data["message"].get("thinking", "")

        # If content is empty, extract the answer from the END of thinking
        if not text and thinking:
            text = _extract_answer_from_thinking(thinking)
        elif not text:
            return "", 0

        # Extract token counts from Ollama response
        prompt_tokens = data.get("prompt_eval_count", 0)
        eval_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + eval_tokens
        return text, total_tokens
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return "", 0


def _extract_answer_from_thinking(thinking: str) -> str:
    """Extract the final answer from qwen3.5's thinking block.

    The model usually ends with patterns like:
    - "Final Answer: X"
    - "Answer: X"
    - "**X**"
    - A standalone short line at the end
    """
    import re
    lines = [l.strip() for l in thinking.split("\n") if l.strip()]
    if not lines:
        return ""

    # Try patterns first (most specific). Require substantial content (not just punctuation).
    for pattern in [
        r"(?:final\s+)?answer\s*[:=]\s*['\"]?([A-Za-z][^\.\n,'\"]{0,60})",
        r"final\s+output\s*[:=]\s*['\"]?([A-Za-z][^\.\n,'\"]{0,60})",
        r"the\s+answer\s+is\s*[:=]?\s*['\"]?([A-Za-z][^\.\n,'\"]{0,60})",
        r"\*\*\s*([A-Za-z][^*\n]{1,60}?)\s*\*\*",  # Bold text with content
    ]:
        for line in reversed(lines):
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                ans = m.group(1).strip().rstrip(".'\"")
                if ans and len(ans) >= 1:
                    return ans

    # Fallback: take the last non-numbered, non-process line
    skip_prefixes = ("thinking", "process", "analysis", "step", "match", "extract", "formulate", "check", "context", "input", "constraint", "strategy", "rule", "note", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-", "*")
    for line in reversed(lines):
        if not line.lower().startswith(skip_prefixes) and len(line) < 80:
            cleaned = line.lstrip("*").rstrip("*").strip()
            # Skip lines that are just punctuation
            if any(c.isalnum() for c in cleaned):
                return cleaned

    return lines[-1]


def _parse_json_from_text(text: str) -> dict | None:
    """Try to extract JSON from LLM response text."""
    # Try to find JSON block in the text
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None


def actor_answer(
    example: QAExample,
    attempt_id: int,
    agent_type: str,
    reflection_memory: list[str],
) -> tuple[str, int]:
    """Call LLM to answer the question using context."""
    # Truncate context to keep prompts small and fast
    context_text = "\n\n".join(
        f"[{c.title}]: {c.text[:300]}" for c in example.context[:6]
    )

    user_msg = f"Context:\n{context_text}\n\nQuestion: {example.question}"

    # Choose system prompt based on agent type and attempt
    if agent_type == "react" or attempt_id == 1:
        system = ACTOR_REACT_SYSTEM  # Force ReAct-like behavior even on first attempt of reflexion
    else:
        # attempt 2+ of reflexion: use the stronger prompt with reflection focus
        system = ACTOR_REFLEXION_SYSTEM

    if reflection_memory:
        reflections = "\n".join(f"- {r}" for r in reflection_memory[-2:])  # Only last 2 reflections
        user_msg += f"\n\nReflections:\n{reflections}"

    response, tokens = _call_ollama(system, user_msg)
    # Clean up the response - extract just the answer
    answer = response.strip()
    # Remove common prefixes
    for prefix in ["Answer:", "The answer is:", "Final answer:", "A:"]:
        if answer.lower().startswith(prefix.lower()):
            answer = answer[len(prefix):].strip()
    # Take only first line/short answer
    answer = answer.split("\n")[0].strip()
    return answer, tokens


def evaluator(example: QAExample, answer: str) -> tuple[JudgeResult, int]:
    """Evaluate if the predicted answer matches the gold answer.

    Primary: exact substring/normalized match (fast, deterministic).
    Secondary: LLM evaluator for ambiguous cases.
    """
    gold_n = normalize_answer(example.gold_answer)
    pred_n = normalize_answer(answer)
    tokens = 0

    if not gold_n or not pred_n:
        return JudgeResult(score=0, reason="Empty answer", missing_evidence=[example.gold_answer], spurious_claims=[answer]), 0

    # Reject very short single-character predictions (avoid 'n' matching 'honolulu' as substring)
    if len(pred_n) < 2 and len(gold_n) > 3:
        return JudgeResult(score=0, reason=f"Predicted answer too short: '{answer}'"), 0

    # Primary: gold answer appears as a whole word/phrase in the predicted answer
    # Use word-boundary match to avoid 'n' substring matching 'honolulu'
    import re
    if len(gold_n) >= 3 and re.search(rf"\b{re.escape(gold_n)}\b", pred_n):
        return JudgeResult(score=1, reason=f"Match: '{answer}' contains gold '{example.gold_answer}'"), 0
    if len(pred_n) >= 3 and re.search(rf"\b{re.escape(pred_n)}\b", gold_n):
        return JudgeResult(score=1, reason=f"Match: gold '{example.gold_answer}' contains predicted '{answer}'"), 0

    # Token-level overlap: split into words
    gold_words = set(gold_n.split())
    pred_words = set(pred_n.split())
    # Remove very short tokens that cause false matches
    gold_words = {w for w in gold_words if len(w) >= 2}
    pred_words = {w for w in pred_words if len(w) >= 2}
    if gold_words and pred_words:
        overlap = len(gold_words & pred_words)
        if overlap > 0 and gold_words.issubset(pred_words):
            return JudgeResult(score=1, reason=f"Gold tokens all present in prediction"), 0

    # LLM evaluator for ambiguous cases
    user_msg = (
        f"Question: {example.question}\n"
        f"Gold answer: {example.gold_answer}\n"
        f"Predicted answer: {answer}\n\n"
        f"Is the predicted answer correct? Answer with JSON: {{\"score\": 0 or 1, \"reason\": \"...\"}}"
    )
    response, tokens = _call_ollama(EVALUATOR_SYSTEM, user_msg)
    parsed = _parse_json_from_text(response)
    if parsed and "score" in parsed:
        return JudgeResult(
            score=int(parsed["score"]),
            reason=parsed.get("reason", "LLM evaluation"),
            missing_evidence=parsed.get("missing_evidence", []),
            spurious_claims=parsed.get("spurious_claims", [answer]),
        ), tokens

    return JudgeResult(
        score=0,
        reason=f"No match. Gold='{example.gold_answer}' Pred='{answer}'",
        missing_evidence=[example.gold_answer],
        spurious_claims=[answer],
    ), tokens


def reflector(
    example: QAExample, attempt_id: int, judge: JudgeResult
) -> tuple[ReflectionEntry, int]:
    """Call LLM to reflect on the failure and propose a strategy."""
    context_text = "\n\n".join(
        f"[{c.title}]: {c.text}" for c in example.context
    )

    user_msg = (
        f"Context:\n{context_text}\n\n"
        f"Question: {example.question}\n"
        f"Wrong answer: {judge.spurious_claims[0] if judge.spurious_claims else 'N/A'}\n"
        f"Reason it was wrong: {judge.reason}\n"
        f"Missing evidence: {', '.join(judge.missing_evidence) if judge.missing_evidence else 'N/A'}\n\n"
        f"Analyze the failure and propose a better strategy. Respond in JSON format."
    )

    response, tokens = _call_ollama(REFLECTOR_SYSTEM, user_msg)

    parsed = _parse_json_from_text(response)
    if parsed:
        return ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=parsed.get("failure_reason", judge.reason),
            lesson=parsed.get("lesson", "Need to re-examine context more carefully."),
            next_strategy=parsed.get("next_strategy", "Re-read all context passages before answering."),
        ), tokens

    # Fallback reflection
    return ReflectionEntry(
        attempt_id=attempt_id,
        failure_reason=judge.reason,
        lesson="Need to re-examine context more carefully.",
        next_strategy="Re-read all context passages and chain information step by step.",
    ), tokens
