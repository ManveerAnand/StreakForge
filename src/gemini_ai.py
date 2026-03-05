"""
StreakForge — Gemini AI Client
Multi-key rotation with automatic failover.
Two thinking tiers: low (fast automation) and high (deep reasoning).
"""

import json
import logging
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEYS,
    GEMINI_MODEL,
    GEMINI_THINKING_LOW,
    GEMINI_THINKING_HIGH,
    PROMPTS_DIR,
)

logger = logging.getLogger("streakforge.gemini")

# ──────────────────── Multi-Key Client Pool ────────────────────

_clients: list[genai.Client] = []
_current_key_idx: int = 0


def _init_clients() -> None:
    """Build a client for each available API key."""
    global _clients
    if _clients:
        return
    if not GEMINI_API_KEYS:
        raise RuntimeError(
            "No Gemini API keys configured. Set GEMINI_API_KEYS, GEMINI_API_KEY_1..N, or GEMINI_API_KEY.")
    _clients = [genai.Client(api_key=k) for k in GEMINI_API_KEYS]
    logger.info("Initialized %d Gemini API key(s)", len(_clients))


def _next_client() -> genai.Client:
    """Round-robin to the next API key."""
    global _current_key_idx
    _init_clients()
    client = _clients[_current_key_idx % len(_clients)]
    _current_key_idx = (_current_key_idx + 1) % len(_clients)
    return client


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = Path(PROMPTS_DIR) / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def _extract_code_from_raw(raw: str) -> str:
    """
    Best-effort extraction of Python code from a malformed AI response.
    Tries, in order:
    1. Code inside ```python ... ``` fences
    2. Code inside ```...``` fences that contains 'class Solution'
    3. Everything from 'class Solution' to the end
    """
    # Try: ```python\n...\n```
    match = re.search(r"```python\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try: any fenced block with class Solution
    match = re.search(r"```\w*\s*\n(.*?class Solution.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: grab from 'class Solution' to the end (or next non-code section)
    match = re.search(r"(class Solution.*?)(?:\n\n[A-Z]|\Z)", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Nothing worked — return raw and hope for the best
    logger.warning("Could not extract code from raw AI response")
    return raw.strip()


def _is_retryable(error_str: str) -> bool:
    """Check if the error is a transient overload / quota issue."""
    markers = ("503", "UNAVAILABLE", "overloaded",
               "429", "RESOURCE_EXHAUSTED", "quota")
    lower = error_str.lower()
    return any(m.lower() in lower for m in markers)


def _generate(prompt: str, thinking_level: str = GEMINI_THINKING_LOW) -> str:
    """
    Generate content using Gemini with multi-key rotation.

    Strategy:
    1. Try the current key (round-robin).
    2. On 503 / 429 / quota error → rotate to the next key immediately.
    3. Cycle through ALL keys before giving up.
    4. If every key fails, wait 20s and do one final sweep.
    """
    _init_clients()
    num_keys = len(_clients)
    # Total attempts = 2 full sweeps across all keys
    max_attempts = num_keys * 2
    last_error = None

    for attempt in range(1, max_attempts + 1):
        client = _next_client()
        key_num = (_current_key_idx - 1) % num_keys + \
            1  # 1-indexed for logging
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level=thinking_level),
                    temperature=0.7,
                ),
            )
            return response.text
        except Exception as e:
            last_error = e
            error_str = str(e)
            if _is_retryable(error_str):
                logger.warning(
                    "Key #%d hit %s (attempt %d/%d) — rotating...",
                    key_num,
                    error_str[:80],
                    attempt,
                    max_attempts,
                )
                # Brief pause between rotations; longer pause between sweeps
                if attempt == num_keys:
                    logger.info(
                        "All keys exhausted in first sweep. Waiting 20s before retry sweep...")
                    time.sleep(20)
                else:
                    time.sleep(2)
            else:
                # Non-retryable error (auth, bad request, etc.) — fail fast
                raise

    raise RuntimeError(
        f"All {num_keys} Gemini API key(s) exhausted after {max_attempts} attempts. "
        f"Last error: {last_error}"
    )


# ──────────────────── Question Decoding ────────────────────


def decode_question_easy_medium(
    title: str,
    difficulty: str,
    tags: list[str],
    content: str,
    examples: str,
) -> str:
    """
    Decode an Easy/Medium question for the morning message.
    Returns WhatsApp-formatted plain text.
    Uses low thinking (fast, automation tier).
    """
    template = _load_prompt("decode_easy_medium")
    prompt = template.format(
        title=title,
        difficulty=difficulty,
        tags=", ".join(tags),
        content=content,
        examples=examples,
    )
    return _generate(prompt, thinking_level=GEMINI_THINKING_LOW)


def decode_question_hard(
    title: str,
    tags: list[str],
    content: str,
    examples: str,
    constraints: str = "",
) -> dict:
    """
    Decode a Hard question: morning message + 5-level hint sequence.
    Returns dict: { "morning_message": str, "hints": [str, str, str, str, str] }
    Uses high thinking (deep reasoning tier).
    """
    template = _load_prompt("decode_hard")
    prompt = template.format(
        title=title,
        tags=", ".join(tags),
        content=content,
        examples=examples,
        constraints=constraints,
    )
    raw = _generate(prompt, thinking_level=GEMINI_THINKING_HIGH)

    # Parse JSON response
    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]  # remove first line
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        result = json.loads(cleaned)
        return {
            "morning_message": result.get("morning_message", raw),
            "hints": result.get("hints", []),
        }
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse Hard decode response as JSON. Returning raw text.")
        return {"morning_message": raw, "hints": []}


# ──────────────────── Submission Analysis ────────────────────


def analyze_submission(
    title: str,
    difficulty: str,
    tags: list[str],
    description_summary: str,
    status: str,
    language: str,
    code: str,
    total_correct: int,
    total_testcases: int,
    last_testcase: str,
    expected_output: str,
    code_output: str,
    runtime_error: str = "",
    compile_error: str = "",
) -> str:
    """
    Analyze a wrong submission and generate a Socratic hint.
    Returns a 2-4 sentence hint (WhatsApp-formatted).
    Uses high thinking for deep analysis.
    """
    template = _load_prompt("submission_analysis")
    prompt = template.format(
        title=title,
        difficulty=difficulty,
        tags=", ".join(tags),
        description_summary=description_summary,
        status=status,
        language=language,
        code=code,
        totalCorrect=total_correct,
        totalTestcases=total_testcases,
        lastTestcase=last_testcase,
        expectedOutput=expected_output,
        codeOutput=code_output,
        runtimeError=runtime_error or "None",
        compileError=compile_error or "None",
    )
    return _generate(prompt, thinking_level=GEMINI_THINKING_HIGH)


# ──────────────────── Auto-Solve ────────────────────


def generate_solution(
    title: str,
    difficulty: str,
    tags: list[str],
    content: str,
    constraints: str,
    examples: str,
    code_snippet: str,
) -> dict:
    """
    Generate a complete solution with walkthrough and quiz.
    Returns dict: {
        "code": str,
        "approach_name": str,
        "time_complexity": str,
        "space_complexity": str,
        "walkthrough": str,
        "key_insight": str,
        "quiz": {
            "question": str,
            "options": [str, str, str, str],
            "correct_index": int,
            "explanation": str,
        }
    }
    Uses high thinking for deep reasoning.
    """
    template = _load_prompt("auto_solve")
    prompt = template.format(
        title=title,
        difficulty=difficulty,
        tags=", ".join(tags),
        content=content,
        constraints=constraints,
        examples=examples,
        code_snippet=code_snippet,
    )
    raw = _generate(prompt, thinking_level=GEMINI_THINKING_HIGH)

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Failed to parse auto-solve response as JSON. Attempting code extraction...")
        # Try to extract just the Python code from the raw response
        code = _extract_code_from_raw(raw)
        return {
            "code": code,
            "approach_name": "Unknown",
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "walkthrough": "",
            "key_insight": "",
            "quiz": None,
        }


# ──────────────────── Reminder Text ────────────────────


def generate_reminder_text(
    title: str,
    difficulty: str,
    reminder_number: int,
    is_hard: bool = False,
) -> str:
    """
    Generate contextual reminder text.
    reminder_number: 1-4 (10AM, 2PM, 6PM, 9PM)
    Uses low thinking (fast).
    """
    tone_map = {
        1: "casual and friendly — no rush, just a light nudge",
        2: "encouraging — good time to take a crack at it",
        3: "warm urgency — evening is here, keep the streak alive",
        4: "serious but supportive — last reminder, auto-solve coming at 11:45 PM",
    }
    tone = tone_map.get(reminder_number, tone_map[1])

    prompt = f"""Generate a SHORT reminder message (2-3 sentences max) for a LeetCode daily challenge.

Problem: {title} ({difficulty})
Tone: {tone}
Reminder #{reminder_number} of 4 today.

Rules:
- WhatsApp formatting (*bold*, _italic_)
- Include the problem name
- {"Mention that this is a Hard one but they can do it" if is_hard else ""}
- If reminder #4, mention auto-solve at 11:45 PM
- Keep it under 50 words
- Be genuine, not robotic"""

    return _generate(prompt, thinking_level=GEMINI_THINKING_LOW)


# ──────────────────── Congratulations ────────────────────


def generate_congrats(title: str, difficulty: str) -> str:
    """Generate a short congratulatory message when the user solves the question."""
    prompt = f"""Generate a SHORT congratulatory message (1-2 sentences) for solving a LeetCode problem.

Problem: {title} ({difficulty})

Rules:
- WhatsApp formatting
- Be genuinely encouraging
- Mention the difficulty naturally
- Under 30 words
- No emojis overload (1-2 max)"""

    return _generate(prompt, thinking_level=GEMINI_THINKING_LOW)
