"""
StreakForge — Morning Job
Runs at 6:00 AM IST. Fetches the daily challenge, decodes it with AI,
and sends the morning message to WhatsApp + Telegram.
Hard questions get the full 5-hint sequence generated and cached.
"""

import logging
import sys

from src import leetcode_api, gemini_ai, notifier, formatter
from src.state import (
    load_state, save_state, ensure_today_fresh,
    mark_morning_sent, store_hints, is_solved_today, mark_solved,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("streakforge.morning")


def run():
    logger.info("═══ StreakForge Morning Job Started ═══")

    # 1. Load & freshen state
    state = load_state()
    state = ensure_today_fresh(state)

    # Check if morning message already sent (idempotency for retries)
    if state["today"]["morning_sent"]:
        logger.info("Morning message already sent today. Skipping.")
        save_state(state)
        return

    # 2. Fetch daily challenge
    logger.info("Fetching daily challenge from LeetCode...")
    try:
        question = leetcode_api.get_daily_challenge()
    except Exception as e:
        logger.error("Failed to fetch daily challenge: %s", e)
        notifier.send_alert(
            f"Failed to fetch today's LeetCode daily challenge.\n\nError: {e}")
        sys.exit(1)

    title = question["title"]
    difficulty = question["difficulty"]
    tags = question["topicTags"]
    content = question["content"]
    link = question["link"]
    date_str = question["date"]
    examples = question["exampleTestcases"]

    logger.info("Today's question: %s (%s) — Tags: %s",
                title, difficulty, tags)

    # 3. Check if already solved (user might have solved it early)
    try:
        if leetcode_api.is_question_solved(question["titleSlug"]):
            logger.info("Question already solved! Sending congrats.")
            state = mark_solved(state)
            congrats = gemini_ai.generate_congrats(title, difficulty)
            msg = formatter.format_solved_congrats(title, congrats)
            notifier.notify(msg)
            state = mark_morning_sent(state, question)
            save_state(state)
            return
    except Exception as e:
        logger.warning("Could not check solve status (session issue?): %s", e)
        # Continue anyway — we'll still send the morning message

    # 4. Decode with AI (different flow for Easy/Medium vs Hard)
    is_hard = difficulty == "Hard"

    if is_hard:
        logger.info("Hard question detected — using deep reasoning tier")
        try:
            result = gemini_ai.decode_question_hard(
                title=title,
                tags=tags,
                content=content,
                examples=examples,
            )
            morning_text = result["morning_message"]
            hints = result["hints"]

            # Store hints in state for drip delivery
            if hints:
                state = store_hints(state, hints)
                logger.info(
                    "Generated and cached %d hints for hard question", len(hints))
            else:
                logger.warning("No hints generated for hard question")

        except Exception as e:
            logger.error(
                "Hard decode failed: %s — falling back to simple decode", e)
            morning_text = gemini_ai.decode_question_easy_medium(
                title, difficulty, tags, content, examples)
            is_hard = False  # Treat as normal if AI fails

        msg = formatter.format_morning_hard(
            date_str, title, tags, morning_text, link)

    else:
        logger.info("Easy/Medium question — using automation tier")
        try:
            morning_text = gemini_ai.decode_question_easy_medium(
                title=title,
                difficulty=difficulty,
                tags=tags,
                content=content,
                examples=examples,
            )
        except Exception as e:
            logger.error("Decode failed: %s", e)
            # Fallback: send a basic message without AI decode
            morning_text = (
                f"*What it's really asking:*\n"
                f"Check the problem link below for details.\n\n"
                f"*Tags:* {', '.join(tags)}"
            )

        msg = formatter.format_morning_easy_medium(
            date_str, title, difficulty, tags, morning_text, link)

    # 5. Send to both channels
    logger.info("Sending morning message...")
    result = notifier.notify(msg)
    logger.info("Delivery: WhatsApp=%s, Telegram=%s",
                result["whatsapp"], result["telegram"])

    # 6. Update state
    state = mark_morning_sent(state, question)
    save_state(state)

    logger.info("═══ Morning Job Complete ═══")


if __name__ == "__main__":
    run()
