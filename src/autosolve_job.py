"""
StreakForge — Auto-Solve Job
Runs at 11:45 PM IST. If the daily question is unsolved and auto-solve quota
is available, generates a solution with AI, submits it, and sends the full
learning package (solution + walkthrough + quiz).
"""

import logging
import sys

from src import leetcode_api, gemini_ai, notifier, formatter
from src.state import (
    load_state, save_state, ensure_today_fresh,
    is_solved_today, mark_solved, can_auto_solve,
    get_auto_solves_remaining, mark_auto_solved, mark_quiz_sent,
)
from src.config import MAX_AUTO_SOLVES_PER_WEEK

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("streakforge.autosolve")


def run():
    logger.info("═══ StreakForge Auto-Solve Job Started ═══")

    # 1. Load & freshen state
    state = load_state()
    state = ensure_today_fresh(state)

    title = state["today"]["question_title"]
    slug = state["today"]["question_slug"]
    difficulty = state["today"]["difficulty"]

    if not slug:
        logger.error(
            "No question data in state. Morning job may not have run.")
        notifier.send_alert(
            "Auto-solve triggered but no question data found. Did the morning job run?")
        save_state(state)
        sys.exit(1)

    # 2. Check if already solved
    try:
        solved = leetcode_api.is_question_solved(slug)
    except Exception as e:
        logger.warning("Could not check solve status: %s", e)
        solved = is_solved_today(state)

    if solved or is_solved_today(state):
        logger.info("Question already solved. No auto-solve needed. 🎉")
        if not is_solved_today(state):
            state = mark_solved(state)
            save_state(state)
        return

    # 3. Check auto-solve quota
    if not can_auto_solve(state):
        logger.info("Auto-solve quota exhausted (%d/%d this week)",
                    state["auto_solves_this_week"], MAX_AUTO_SOLVES_PER_WEEK)
        msg = formatter.format_autosolve_quota_exceeded(title)
        notifier.notify(msg)
        save_state(state)
        return

    remaining = get_auto_solves_remaining(state)
    logger.info(
        "Auto-solve quota OK (%d remaining this week). Proceeding...", remaining)

    # 4. Fetch full question data (we need code snippets, content, etc.)
    try:
        question = leetcode_api.get_daily_challenge()
    except Exception as e:
        logger.error("Failed to fetch question for auto-solve: %s", e)
        notifier.send_alert(
            f"Auto-solve failed — couldn't fetch question data.\n\nError: {e}")
        save_state(state)
        sys.exit(1)

    code_snippet = leetcode_api.get_python3_snippet(question["codeSnippets"])
    if not code_snippet:
        logger.error("No Python3 code snippet found for %s", slug)
        notifier.send_alert(
            f"Auto-solve failed — no Python3 code snippet available for *{title}*.")
        save_state(state)
        sys.exit(1)

    # 5. Generate solution with AI
    logger.info("Generating solution with Gemini (deep reasoning)...")
    try:
        solution = gemini_ai.generate_solution(
            title=title,
            difficulty=difficulty,
            tags=question["topicTags"],
            content=question["content"],
            constraints="(see problem description)",
            examples=question["exampleTestcases"],
            code_snippet=code_snippet,
        )
    except Exception as e:
        logger.error("AI solution generation failed: %s", e)
        notifier.send_alert(
            f"Auto-solve failed — AI couldn't generate a solution for *{title}*.\n\nError: {e}")
        save_state(state)
        sys.exit(1)

    code = solution.get("code", "")
    if not code:
        logger.error("AI returned empty code")
        notifier.send_alert(
            f"Auto-solve failed — AI returned an empty solution for *{title}*.")
        save_state(state)
        sys.exit(1)

    # 6. Submit to LeetCode
    logger.info("Submitting solution to LeetCode...")
    try:
        result = leetcode_api.submit_solution(
            title_slug=slug,
            question_id=question["questionId"],
            code=code,
        )
    except Exception as e:
        logger.error("Submission failed: %s", e)
        notifier.send_alert(
            f"Auto-solve submission failed for *{title}*.\n\nError: {e}")
        save_state(state)
        sys.exit(1)

    if not result.get("passed"):
        logger.warning("Submitted solution was NOT accepted: %s",
                       result.get("status_display"))
        # Try once more with a hint about the failure
        logger.info("Retrying with failure context...")
        try:
            # Re-generate with failure context
            retry_prompt_suffix = f"\n\nIMPORTANT: A previous solution attempt got '{result.get('status_display')}'. Make sure to handle edge cases carefully."
            solution_retry = gemini_ai.generate_solution(
                title=title,
                difficulty=difficulty,
                tags=question["topicTags"],
                content=question["content"] + retry_prompt_suffix,
                constraints="(see problem description)",
                examples=question["exampleTestcases"],
                code_snippet=code_snippet,
            )
            code_retry = solution_retry.get("code", "")
            if code_retry:
                result = leetcode_api.submit_solution(
                    title_slug=slug,
                    question_id=question["questionId"],
                    code=code_retry,
                )
                if result.get("passed"):
                    solution = solution_retry
                    code = code_retry
                    logger.info("Retry succeeded!")
                else:
                    logger.error("Retry also failed: %s",
                                 result.get("status_display"))
        except Exception as e:
            logger.error("Retry failed: %s", e)

    # 7. Update state regardless of pass/fail
    if result.get("passed"):
        state = mark_auto_solved(state)
        state = mark_solved(state)
        logger.info("✅ Solution accepted!")
    else:
        logger.warning("Solution not accepted, but updating state anyway.")
        # Still counts as an auto-solve attempt
        state = mark_auto_solved(state)

    # 8. Send the learning package (regardless of acceptance)
    auto_solves_used = state["auto_solves_this_week"]

    # Message 1: Status
    msg_status = formatter.format_autosolve_status(
        title, difficulty, auto_solves_used)
    notifier.notify(msg_status)

    # Message 2: Solution code
    msg_solution = formatter.format_autosolve_solution(
        title=title,
        approach_name=solution.get("approach_name", "See code"),
        time_complexity=solution.get("time_complexity", "See analysis"),
        space_complexity=solution.get("space_complexity", "See analysis"),
        code=code,
    )
    notifier.notify(msg_solution)

    # Message 3: Walkthrough
    walkthrough = solution.get("walkthrough", "")
    key_insight = solution.get("key_insight", "")
    if walkthrough:
        msg_walkthrough = formatter.format_autosolve_walkthrough(
            walkthrough, key_insight)
        notifier.notify(msg_walkthrough)

    # Message 4: Quiz
    quiz = solution.get("quiz")
    if quiz and isinstance(quiz, dict):
        question_text = quiz.get("question", "")
        options = quiz.get("options", [])

        if question_text and options:
            # WhatsApp: text-based quiz
            wa_quiz = formatter.format_quiz_whatsapp(question_text, options)
            # Telegram: interactive buttons
            tg_question = formatter.format_quiz_telegram(question_text)
            notifier.notify_quiz(wa_quiz, tg_question, options)

            state = mark_quiz_sent(state, quiz)
            logger.info("Quiz sent via both channels")
    else:
        logger.warning("No quiz data generated")

    # 9. Save state
    save_state(state)

    acceptance = "ACCEPTED ✅" if result.get(
        "passed") else f"NOT ACCEPTED ({result.get('status_display', '?')})"
    logger.info("═══ Auto-Solve Complete — %s ═══", acceptance)


if __name__ == "__main__":
    run()
