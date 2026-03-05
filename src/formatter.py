"""
StreakForge — Message Formatter
Crafts the actual messages that land on the user's phone.
Separate formatters for WhatsApp (plain text) and Telegram (Markdown).
"""

from src.config import MAX_AUTO_SOLVES_PER_WEEK


# ──────────────────── Morning Messages ────────────────────


def format_morning_easy_medium(
    date_str: str,
    title: str,
    difficulty: str,
    tags: list[str],
    decoded_text: str,
    link: str,
) -> str:
    """Format the morning message for Easy/Medium questions."""
    emoji = "🟢" if difficulty == "Easy" else "🟡"
    tags_str = ", ".join(tags)

    return (
        f"☀️ *LeetCode Daily — {date_str}*\n"
        f"\n"
        f"📌 *{title}* ({emoji} {difficulty})\n"
        f"🏷️ {tags_str}\n"
        f"\n"
        f"{decoded_text}\n"
        f"\n"
        f"🔗 {link}\n"
    )


def format_morning_hard(
    date_str: str,
    title: str,
    tags: list[str],
    decoded_text: str,
    link: str,
) -> str:
    """Format the morning message for Hard questions."""
    tags_str = ", ".join(tags)

    return (
        f"🔴 *LeetCode Daily — {date_str}*\n"
        f"\n"
        f"📌 *{title}* (🔴 Hard)\n"
        f"🏷️ {tags_str}\n"
        f"\n"
        f"Don't be intimidated. Let's break this down.\n"
        f"\n"
        f"{decoded_text}\n"
        f"\n"
        f"🔗 {link}\n"
    )


# ──────────────────── Hints ────────────────────


def format_hint_message(
    title: str,
    hint_level: int,
    hint_text: str,
    has_more: bool = True,
) -> str:
    """Format a progressive hint delivery message."""
    level_labels = {
        1: "Pattern Recognition",
        2: "Approach Direction",
        3: "Key Mechanics",
        4: "Implementation Nudge",
        5: "Near-Solution Conceptual",
    }
    label = level_labels.get(hint_level, f"Level {hint_level}")

    msg = (
        f"💡 *Hint {hint_level}/5 — {label}*\n"
        f"\n"
        f"{hint_text}\n"
    )

    if has_more:
        msg += f"\n_Send 'hint' on Telegram for the next level._"
    else:
        msg += f"\n_That's all the hints! The rest is up to you. You've got this. 💪_"

    return msg


def format_submission_hint(
    title: str,
    status: str,
    passed: str,
    hint_text: str,
) -> str:
    """Format a submission-aware Socratic hint."""
    return (
        f"🔍 *{title}* — Quick nudge\n"
        f"\n"
        f"_{status} ({passed} test cases passed)_\n"
        f"\n"
        f"{hint_text}\n"
    )


# ──────────────────── Reminders ────────────────────


def format_reminder(
    title: str,
    difficulty: str,
    reminder_text: str,
    reminder_number: int,
) -> str:
    """Format a reminder message."""
    emoji_map = {1: "⏰", 2: "📝", 3: "🌙", 4: "⚠️"}
    emoji = emoji_map.get(reminder_number, "⏰")

    return f"{emoji} {reminder_text}"


def format_solved_congrats(title: str, congrats_text: str) -> str:
    """Format a congratulatory message when the question is solved."""
    return f"🎉 {congrats_text}"


# ──────────────────── Auto-Solve ────────────────────


def format_autosolve_status(
    title: str,
    difficulty: str,
    auto_solves_used: int,
) -> str:
    """Format the auto-solve activation status message (Message 1)."""
    return (
        f"✅ *Auto-Solve Activated*\n"
        f"\n"
        f"I've submitted a solution for today's *{title}* ({difficulty}).\n"
        f"\n"
        f"Your streak is safe. 🔥\n"
        f"Auto-solves used this week: {auto_solves_used}/{MAX_AUTO_SOLVES_PER_WEEK}\n"
        f"\n"
        f"Let me walk you through the solution. 👇"
    )


def format_autosolve_solution(
    title: str,
    approach_name: str,
    time_complexity: str,
    space_complexity: str,
    code: str,
) -> str:
    """Format the solution message (Message 2)."""
    return (
        f"📝 *Solution: {title}*\n"
        f"\n"
        f"*Approach:* {approach_name}\n"
        f"*Time:* {time_complexity} | *Space:* {space_complexity}\n"
        f"\n"
        f"```python\n{code}\n```\n"
    )


def format_autosolve_walkthrough(walkthrough: str, key_insight: str) -> str:
    """Format the step-by-step walkthrough (Message 3)."""
    return (
        f"🧠 *Walkthrough*\n"
        f"\n"
        f"{walkthrough}\n"
        f"\n"
        f"*The key insight:*\n"
        f"{key_insight}\n"
    )


def format_quiz_whatsapp(question: str, options: list[str]) -> str:
    """Format quiz for WhatsApp (text-based, reply with A/B/C/D)."""
    options_text = "\n".join(options)
    return (
        f"📋 *Quick Check — Did you get it?*\n"
        f"\n"
        f"{question}\n"
        f"\n"
        f"{options_text}\n"
        f"\n"
        f"_Reply with A, B, C, or D_"
    )


def format_quiz_telegram(question: str) -> str:
    """Format quiz question for Telegram (buttons are sent separately via reply_markup)."""
    return f"📋 *Quick Check — Did you get it?*\n\n{question}"


# ──────────────────── Alerts ────────────────────


def format_session_expired() -> str:
    """Format session expiry alert."""
    return (
        "🔑 Your LeetCode session has expired!\n"
        "\n"
        "StreakForge can't check your solve status or auto-submit until you update it.\n"
        "\n"
        "*How to fix:*\n"
        "1. Log into LeetCode in your browser\n"
        "2. Open DevTools → Application → Cookies\n"
        "3. Copy `LEETCODE_SESSION` and `csrftoken`\n"
        "4. Update them in GitHub repo → Settings → Secrets\n"
        "\n"
        "_This takes ~2 minutes._"
    )


def format_autosolve_quota_exceeded(title: str) -> str:
    """Format message when auto-solve quota is used up."""
    return (
        f"⚠️ *{title}* is still unsolved.\n"
        f"\n"
        f"You've used both auto-solves this week.\n"
        f"Tonight's streak depends on you.\n"
        f"\n"
        f"_You've got until midnight. I believe in you._ 💪"
    )
