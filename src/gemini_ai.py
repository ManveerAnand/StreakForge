"""
StreakForge — Gemini AI Client
Two-tier AI: automation (thinking=low) and reasoning (thinking=high).
Handles question decoding, hint generation, submission analysis, auto-solve, and quizzes.
"""

import json
import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_AUTOMATION,
    GEMINI_MODEL_REASONING,
    GEMINI_THINKING_LOW,
    GEMINI_THINKING_HIGH,
    PROMPTS_DIR,
)

logger = logging.getLogger("streakforge.gemini")

# ──────────────────── Client Setup ────────────────────

_client = None


def _get_client() -> genai.Client:
    """Lazy-init the Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = Path(PROMPTS_DIR) / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def _generate(prompt: str, thinking_level: str = GEMINI_THINKING_LOW) -> str:
    """
    Generate content using Gemini.
    thinking_level: 'low' for automation, 'high' for deep reasoning.
    """
    client = _get_client()
    model = GEMINI_MODEL_AUTOMATION if thinking_level == GEMINI_THINKING_LOW else GEMINI_MODEL_REASONING

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_level=thinking_level),
            temperature=0.7,
        ),
    )
    return response.text


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
        logger.error("Failed to parse auto-solve response as JSON.")
        # Return minimal structure so the flow doesn't crash
        return {
            "code": raw,
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
