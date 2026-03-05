"""
StreakForge — State Management
Persistent state stored in state.json, committed to the repo by GitHub Actions.
Tracks: auto-solve quota, today's progress, hint levels, analyzed submissions.
"""

import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.config import STATE_FILE, TIMEZONE, MAX_AUTO_SOLVES_PER_WEEK

logger = logging.getLogger("streakforge.state")

IST = ZoneInfo(TIMEZONE)


def _now_ist() -> datetime:
    return datetime.now(IST)


def _today_str() -> str:
    return _now_ist().date().isoformat()


def _monday_of_week(d: date) -> str:
    """Get ISO date string of the Monday of the week containing date d."""
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def _default_state() -> dict:
    """Return a fresh default state."""
    today = _now_ist().date()
    return {
        "version": 1,
        "week_start": _monday_of_week(today),
        "auto_solves_this_week": 0,
        "auto_solve_dates": [],
        "today": _default_today(),
        "session_last_verified": "",
        "session_healthy": True,
        "last_keepalive": "",
    }


def _default_today() -> dict:
    """Return a fresh 'today' state block."""
    return {
        "date": _today_str(),
        "question_slug": "",
        "question_title": "",
        "difficulty": "",
        "tags": [],
        "is_solved": False,
        "morning_sent": False,
        "hints_generated": False,
        "hints_cache": [],
        "current_hint_level": 0,
        "hints_delivered": [],
        "reminders_sent": [],
        "submissions_analyzed": [],
        "auto_solved": False,
        "quiz_sent": False,
        "quiz_answered": False,
        "quiz_correct": None,
        "quiz_data": None,
    }


# ──────────────────── Read / Write ────────────────────


def load_state() -> dict:
    """Load state from state.json. Returns default state if file doesn't exist or is corrupted."""
    path = Path(STATE_FILE)
    if not path.exists():
        logger.info("state.json not found — creating default state")
        state = _default_state()
        save_state(state)
        return state

    try:
        raw = path.read_text(encoding="utf-8")
        state = json.loads(raw)
        state = _migrate_state(state)
        return state
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("state.json corrupted (%s) — resetting to default", e)
        state = _default_state()
        save_state(state)
        return state


def save_state(state: dict) -> None:
    """Write state to state.json."""
    path = Path(STATE_FILE)
    path.write_text(json.dumps(state, indent=2,
                    ensure_ascii=False), encoding="utf-8")
    logger.info("State saved to %s", STATE_FILE)


def _migrate_state(state: dict) -> dict:
    """Ensure state has all required fields (forward compatibility)."""
    defaults = _default_state()
    for key in defaults:
        if key not in state:
            state[key] = defaults[key]

    today_defaults = _default_today()
    if "today" in state and isinstance(state["today"], dict):
        for key in today_defaults:
            if key not in state["today"]:
                state["today"][key] = today_defaults[key]

    return state


# ──────────────────── Day & Week Transitions ────────────────────


def ensure_today_fresh(state: dict) -> dict:
    """
    If the date has changed, reset today's state block.
    Call this at the start of every job.
    """
    current_date = _today_str()
    if state.get("today", {}).get("date") != current_date:
        logger.info("New day detected (%s → %s) — resetting today's state",
                    state["today"].get("date"), current_date)
        state["today"] = _default_today()
        state["today"]["date"] = current_date

    # Weekly reset (if it's a new week)
    today = _now_ist().date()
    current_week_start = _monday_of_week(today)
    if state.get("week_start") != current_week_start:
        logger.info("New week detected — resetting auto-solve quota")
        state["week_start"] = current_week_start
        state["auto_solves_this_week"] = 0
        state["auto_solve_dates"] = []

    return state


# ──────────────────── Getters ────────────────────


def can_auto_solve(state: dict) -> bool:
    """Check if auto-solve quota is available for this week."""
    return state.get("auto_solves_this_week", 0) < MAX_AUTO_SOLVES_PER_WEEK


def get_auto_solves_remaining(state: dict) -> int:
    """How many auto-solves are left this week."""
    return MAX_AUTO_SOLVES_PER_WEEK - state.get("auto_solves_this_week", 0)


def is_solved_today(state: dict) -> bool:
    """Check if today's question has been solved (per cached state)."""
    return state.get("today", {}).get("is_solved", False)


def get_current_hint_level(state: dict) -> int:
    """Get the current hint level for today's hard question (0-5)."""
    return state.get("today", {}).get("current_hint_level", 0)


def get_hints_cache(state: dict) -> list[str]:
    """Get cached hints for today's hard question."""
    return state.get("today", {}).get("hints_cache", [])


def was_submission_analyzed(state: dict, submission_id: str) -> bool:
    """Check if a submission has already been analyzed (to avoid duplicate hints)."""
    return submission_id in state.get("today", {}).get("submissions_analyzed", [])


# ──────────────────── Setters ────────────────────


def mark_morning_sent(state: dict, question_data: dict) -> dict:
    """Mark the morning message as sent and store question metadata."""
    state["today"]["morning_sent"] = True
    state["today"]["question_slug"] = question_data.get("titleSlug", "")
    state["today"]["question_title"] = question_data.get("title", "")
    state["today"]["difficulty"] = question_data.get("difficulty", "")
    state["today"]["tags"] = question_data.get("topicTags", [])
    return state


def store_hints(state: dict, hints: list[str]) -> dict:
    """Store the generated hint sequence for today's hard question."""
    state["today"]["hints_generated"] = True
    state["today"]["hints_cache"] = hints
    # Level 1 is the morning message itself
    state["today"]["current_hint_level"] = 1
    state["today"]["hints_delivered"] = [1]
    return state


def advance_hint_level(state: dict) -> tuple[dict, str | None]:
    """
    Advance to the next hint level and return the hint text.
    Returns (updated_state, hint_text) or (state, None) if no more hints.
    """
    current = state["today"]["current_hint_level"]
    hints = state["today"]["hints_cache"]

    next_level = current + 1
    if next_level > 5 or next_level - 1 >= len(hints):
        return state, None  # No more hints

    hint_text = hints[next_level - 1]  # hints[0] = level 1, etc.
    state["today"]["current_hint_level"] = next_level
    state["today"]["hints_delivered"].append(next_level)
    return state, hint_text


def mark_solved(state: dict) -> dict:
    """Mark today's question as solved."""
    state["today"]["is_solved"] = True
    return state


def mark_auto_solved(state: dict) -> dict:
    """Mark today as auto-solved and decrement weekly quota."""
    state["today"]["auto_solved"] = True
    state["auto_solves_this_week"] = state.get("auto_solves_this_week", 0) + 1
    state["auto_solve_dates"].append(_today_str())
    return state


def record_reminder(state: dict, time_slot: str) -> dict:
    """Record that a reminder was sent at the given time slot."""
    if time_slot not in state["today"]["reminders_sent"]:
        state["today"]["reminders_sent"].append(time_slot)
    return state


def record_submission_analyzed(state: dict, submission_id: str) -> dict:
    """Record that a submission was analyzed (prevent duplicate hints)."""
    if submission_id not in state["today"]["submissions_analyzed"]:
        state["today"]["submissions_analyzed"].append(submission_id)
    return state


def mark_quiz_sent(state: dict, quiz_data: dict) -> dict:
    """Mark quiz as sent and store quiz data for answer verification."""
    state["today"]["quiz_sent"] = True
    state["today"]["quiz_data"] = quiz_data
    return state


def mark_quiz_answered(state: dict, correct: bool) -> dict:
    """Record quiz answer."""
    state["today"]["quiz_answered"] = True
    state["today"]["quiz_correct"] = correct
    return state


def mark_session_verified(state: dict, healthy: bool) -> dict:
    """Record session health check result."""
    state["session_last_verified"] = _now_ist().isoformat()
    state["session_healthy"] = healthy
    return state
