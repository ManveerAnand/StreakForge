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
LEETCODE_SESSION = os.getenv("LEETCODE_SESSION", "").strip()
CSRF_TOKEN = os.getenv("CSRF_TOKEN", "").strip()

# ─────────────────────────── Gemini AI ─────────────────────────
# Multiple API keys for rotation (load-balance across free-tier quotas).
# Supports:
#   1. Comma-separated in GEMINI_API_KEYS: "key1,key2,key3"
#   2. Individual secrets: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
#   3. Single key fallback: GEMINI_API_KEY
def _load_gemini_keys() -> list[str]:
    """Collect all Gemini API keys from environment variables."""
    keys: list[str] = []
    # Source 1: comma-separated
    bulk = os.getenv("GEMINI_API_KEYS", "").strip()
    if bulk:
        keys.extend(k.strip() for k in bulk.split(",") if k.strip())
    # Source 2: numbered GEMINI_API_KEY_1 .. GEMINI_API_KEY_10
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    # Source 3: single key (backwards compat)
    single = os.getenv("GEMINI_API_KEY", "").strip()
    if single and single not in keys:
        keys.append(single)
    return keys

GEMINI_API_KEYS: list[str] = _load_gemini_keys()

# Model config — single model, different thinking levels
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_THINKING_LOW = "low"       # For easy/medium decode, reminders
# For hard decode, hints, submission analysis, auto-solve
GEMINI_THINKING_HIGH = "high"

# ─────────────────────────── Notifications ─────────────────────
# WhatsApp (CallMeBot)
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "").strip()
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY", "").strip()

# Telegram
TELEGRAM_API_URL_TEMPLATE = "https://api.telegram.org/bot{token}"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

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
