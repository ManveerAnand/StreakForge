"""
StreakForge — Configuration Constants
All tuneable settings in one place. Secrets come from environment variables.
"""

import os

# ─────────────────────────── Timezone ───────────────────────────
TIMEZONE = "Asia/Kolkata"  # IST (UTC+5:30)

# ─────────────────────────── LeetCode ──────────────────────────
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_SUBMIT_URL_TEMPLATE = "https://leetcode.com/problems/{slug}/submit/"
LEETCODE_CHECK_URL_TEMPLATE = "https://leetcode.com/submissions/detail/{id}/check/"

# Auth (from GitHub Secrets → env vars)
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "")
CSRF_TOKEN = os.getenv("CSRF_TOKEN", "")

# ─────────────────────────── Gemini AI ─────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Two-tier model setup: same model, different thinking levels
GEMINI_MODEL_AUTOMATION = "gemini-3-flash-preview"       # Fast tasks
GEMINI_MODEL_REASONING = "gemini-3-flash-preview"        # Deep analysis
GEMINI_THINKING_LOW = "low"       # For easy/medium decode, reminders
# For hard decode, hints, submission analysis, auto-solve
GEMINI_THINKING_HIGH = "high"

# ─────────────────────────── Notifications ─────────────────────
# WhatsApp (CallMeBot)
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY", "")

# Telegram
TELEGRAM_API_URL_TEMPLATE = "https://api.telegram.org/bot{token}"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ─────────────────────────── Streak Rules ──────────────────────
MAX_AUTO_SOLVES_PER_WEEK = 2
SOLUTION_LANGUAGE = "python3"

# ─────────────────────────── Schedule (IST) ────────────────────
MORNING_TIME_IST = "06:00"
REMINDER_TIMES_IST = ["10:00", "14:00", "18:00", "21:00"]
AUTO_SOLVE_TIME_IST = "23:45"

# Hint levels mapped to reminder slots (for time-drip on hard questions)
HINT_DRIP_SCHEDULE = {
    "10:00": 2,  # Level 2 hint at 10 AM
    "14:00": 3,  # Level 3 hint at 2 PM
    "18:00": 4,  # Level 4 hint at 6 PM
    "21:00": 5,  # Level 5 hint at 9 PM
}

# ─────────────────────────── Paths ─────────────────────────────
STATE_FILE = "state.json"
PROMPTS_DIR = "prompts"

# ─────────────────────────── Misc ──────────────────────────────
SUBMISSION_POLL_INTERVAL = 2       # seconds between submission status checks
SUBMISSION_POLL_MAX_RETRIES = 30   # max retries (~60s total)
API_CALL_DELAY = 1                 # seconds between LeetCode API calls
