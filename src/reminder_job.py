"""
StreakForge — Reminder Job
Runs 4 times per day (10 AM, 2 PM, 6 PM, 9 PM IST).
Checks solve status, analyzes wrong submissions, delivers time-drip hints for hard questions.
"""

import logging
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from src import leetcode_api, gemini_ai, notifier, formatter
from src.state import (
    load_state, save_state, ensure_today_fresh,
    is_solved_today, mark_solved, record_reminder,
    get_current_hint_level, get_hints_cache, advance_hint_level,
    was_submission_analyzed, record_submission_analyzed,
)
from src.config import TIMEZONE, HINT_DRIP_SCHEDULE, API_CALL_DELAY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("streakforge.reminder")

IST = ZoneInfo(TIMEZONE)


def _get_reminder_number() -> int:
    """Determine which reminder this is (1-4) based on current IST hour."""
    hour = datetime.now(IST).hour
    if hour < 12:
        return 1   # 10 AM slot
    elif hour < 16:
        return 2   # 2 PM slot
    elif hour < 20:
        return 3   # 6 PM slot
    else:
        return 4   # 9 PM slot


def _get_time_slot() -> str:
    """Get the current reminder time slot string."""
    hour = datetime.now(IST).hour
    if hour < 12:
        return "10:00"
    elif hour < 16:
        return "14:00"
    elif hour < 20:
        return "18:00"
    else:
        return "21:00"


def _today_midnight_timestamp() -> int:
    """Get Unix timestamp for midnight IST today."""
    now = datetime.now(IST)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp())


def run():
    reminder_num = _get_reminder_number()
    time_slot = _get_time_slot()
    logger.info("═══ StreakForge Reminder #%d (%s IST) ═══",
                reminder_num, time_slot)

    # 1. Load & freshen state
    state = load_state()
    state = ensure_today_fresh(state)

    # Check if morning was sent (if not, something's wrong — skip gracefully)
    if not state["today"]["morning_sent"]:
        logger.warning("Morning message not sent yet. Skipping reminder.")
        save_state(state)
        return

    # Check if reminder already sent for this slot (idempotency)
    if time_slot in state["today"]["reminders_sent"]:
        logger.info("Reminder for %s already sent. Skipping.", time_slot)
        save_state(state)
        return

    title = state["today"]["question_title"]
    slug = state["today"]["question_slug"]
    difficulty = state["today"]["difficulty"]
    tags = state["today"]["tags"]
    is_hard = difficulty == "Hard"

    # 2. Check if solved
    try:
        solved = leetcode_api.is_question_solved(slug)
    except Exception as e:
        logger.warning(
            "Could not check solve status: %s — assuming unsolved", e)
        solved = False

    if solved and not is_solved_today(state):
        # Just solved! Send congrats.
        logger.info("Question solved! Sending congratulations.")
        state = mark_solved(state)
        congrats = gemini_ai.generate_congrats(title, difficulty)
        msg = formatter.format_solved_congrats(title, congrats)
        notifier.notify(msg)
        state = record_reminder(state, time_slot)
        save_state(state)
        return

    if is_solved_today(state):
        logger.info("Question already solved. No reminder needed.")
        state = record_reminder(state, time_slot)
        save_state(state)
        return

    # 3. Question is UNSOLVED — build the reminder
    logger.info("Question unsolved. Preparing reminder #%d.", reminder_num)

    # 3a. Check for new wrong submissions (submission-aware hinting)
    submission_hint = None
    if is_hard or True:  # Analyze submissions for ALL difficulties
        try:
            today_ts = _today_midnight_timestamp()
            wrong_subs = leetcode_api.get_wrong_submissions_today(
                slug, today_ts)

            if wrong_subs:
                # Find the newest unanalyzed submission
                for sub in wrong_subs:
                    sub_id = str(sub["id"])
                    if not was_submission_analyzed(state, sub_id):
                        logger.info(
                            "New wrong submission found: id=%s status=%s", sub_id, sub["statusDisplay"])

                        # Fetch details
                        time.sleep(API_CALL_DELAY)
                        detail = leetcode_api.get_submission_detail(
                            int(sub_id))

                        # Analyze with AI
                        submission_hint = gemini_ai.analyze_submission(
                            title=title,
                            difficulty=difficulty,
                            tags=tags,
                            description_summary=f"{title} ({difficulty}) — Tags: {', '.join(tags)}",
                            status=sub["statusDisplay"],
                            language=detail.get("lang", {}).get(
                                "name", "Unknown"),
                            code=detail.get("code", ""),
                            total_correct=detail.get("totalCorrect", 0),
                            total_testcases=detail.get("totalTestcases", 0),
                            last_testcase=detail.get("lastTestcase", ""),
                            expected_output=detail.get("expectedOutput", ""),
                            code_output=detail.get("codeOutput", ""),
                            runtime_error=detail.get("runtimeError", ""),
                            compile_error=detail.get("compileError", ""),
                        )

                        state = record_submission_analyzed(state, sub_id)
                        logger.info(
                            "Submission analyzed. Socratic hint generated.")
                        break  # Only analyze one per reminder cycle

        except Exception as e:
            logger.warning("Submission analysis failed: %s", e)

    # 3b. Build the reminder message
    messages = []

    # Standard reminder text
    try:
        reminder_text = gemini_ai.generate_reminder_text(
            title, difficulty, reminder_num, is_hard)
    except Exception:
        # Fallback reminders
        fallbacks = {
            1: f"Hey, today's LeetCode is still waiting — *{title}* ({difficulty}). You've got this! 🎯",
            2: f"Afternoon check-in: *{title}* still unsolved. Good time to take a crack at it! ⏰",
            3: f"Evening reminder: *{title}* is still open. Let's keep the streak alive! 🔥",
            4: f"⚠️ Last call — *{title}* unsolved. Auto-solve kicks in at 11:45 PM.",
        }
        reminder_text = fallbacks.get(reminder_num, fallbacks[1])

    messages.append(formatter.format_reminder(
        title, difficulty, reminder_text, reminder_num))

    # Submission-aware hint (if we have one)
    if submission_hint:
        # Find the sub we analyzed for the passed/total info
        for sub in wrong_subs:
            if str(sub["id"]) in state["today"]["submissions_analyzed"]:
                passed = f"{detail.get('totalCorrect', '?')}/{detail.get('totalTestcases', '?')}"
                sub_msg = formatter.format_submission_hint(
                    title, sub["statusDisplay"], passed, submission_hint)
                messages.append(sub_msg)
                break

    # Time-drip hint for HARD questions
    if is_hard and state["today"]["hints_generated"]:
        target_level = HINT_DRIP_SCHEDULE.get(time_slot, 0)
        current_level = get_current_hint_level(state)

        if target_level > current_level:
            start_level = current_level + 1
            state, new_hints = advance_hint_level(state, target_level)
            for i, hint_text in enumerate(new_hints):
                level = start_level + i
                has_more = level < 5
                hint_msg = formatter.format_hint_message(
                    title, level, hint_text, has_more)
                messages.append(hint_msg)
            if new_hints:
                logger.info("Dripped %d hint(s), now at level %d",
                            len(new_hints), get_current_hint_level(state))

    # 4. Send all messages
    combined = "\n\n───────────────\n\n".join(messages)
    result = notifier.notify(combined)
    logger.info("Delivery: WhatsApp=%s, Telegram=%s",
                result["whatsapp"], result["telegram"])

    # 5. Update state
    state = record_reminder(state, time_slot)
    save_state(state)

    logger.info("═══ Reminder #%d Complete ═══", reminder_num)


if __name__ == "__main__":
    run()
