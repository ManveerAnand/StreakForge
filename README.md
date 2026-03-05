<div align="center">

# 🔥 StreakForge

**AI-powered LeetCode daily challenge companion**

*Adaptive hints · Submission-aware coaching · Streak protection · Auto-solve*

Built with **Gemini AI** · **GitHub Actions** · **WhatsApp** · **Telegram**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Powered by Gemini](https://img.shields.io/badge/AI-Gemini%203%20Flash-orange.svg)](https://ai.google.dev)
[![GitHub Actions](https://img.shields.io/badge/hosted-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)
[![Zero Cost](https://img.shields.io/badge/cost-%240-brightgreen.svg)](#)

</div>

---

## What is StreakForge?

StreakForge is a fully automated system that turns your LeetCode daily challenge into a guided learning experience — delivered straight to your phone via WhatsApp and Telegram.

It doesn't just remind you. It **teaches** you, **adapts** to difficulty, analyzes your **actual submissions**, and **protects your streak** when life gets in the way.

### Key Features

- **Morning Delivery (6:00 AM IST)** — AI-decoded question breakdown with tags, key insights, and edge cases
- **Hard Question Special Treatment** — Progressive 5-level hint system with Socratic guidance instead of info dumps
- **Submission-Aware Coaching** — Detects your wrong submissions, analyzes the failing test cases, and generates contextual indirect hints
- **4 Smart Reminders** — Escalating nudges at 10 AM, 2 PM, 6 PM, and 9 PM with difficulty-appropriate hints dripped over time
- **Auto-Solve at 11:45 PM** — Generates a solution, submits it, then sends a full learning package (solution + walkthrough + quiz). Limited to 2/week so it never becomes a crutch
- **Comprehension Quiz** — After every auto-solve, a multiple-choice quiz tests understanding (interactive buttons on Telegram)
- **On-Demand Hints** — Text `hint`, `tags`, or `status` on Telegram anytime to get help on your schedule
- **Dual Channel** — WhatsApp (broadcast) + Telegram (interactive with buttons and commands)

---

## Daily Timeline

```
 6:00 AM  ┄  Morning delivery — decoded question + tags
10:00 AM  ┄  Reminder #1 — casual nudge (+ submission analysis if applicable)
 2:00 PM  ┄  Reminder #2 — approach hint for Hard questions
 6:00 PM  ┄  Reminder #3 — deeper conceptual nudge
 9:00 PM  ┄  Reminder #4 — final warning, strongest hint
11:45 PM  ┄  Auto-solve — solution + walkthrough + quiz (if unsolved, quota available)
```

---

## Architecture

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────┐
│  GitHub Actions   │────▶│  Python Modules    │────▶│  Your Phone  │
│  (cron triggers)  │     │  (orchestrators)   │     │  WA + TG     │
└──────────────────┘     └───────┬───────────┘     └──────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ LeetCode │ │ Gemini   │ │ State    │
              │ GraphQL  │ │ AI API   │ │ (JSON)   │
              └──────────┘ └──────────┘ └──────────┘
```

### Project Structure

```
StreakForge/
├── .github/workflows/
│   ├── morning.yml              # 6:00 AM IST — fetch + decode + send
│   ├── reminders.yml            # 10AM, 2PM, 6PM, 9PM IST — check + hint + nudge
│   ├── auto_solve.yml           # 11:45 PM IST — generate + submit + teach
│   ├── session_health_check.yml # Weekly session cookie verification
│   └── keepalive.yml            # Monthly commit to prevent Actions disable
├── src/
│   ├── config.py                # Constants, env vars, schedule configuration
│   ├── leetcode_api.py          # LeetCode GraphQL client (fetch, submit, verify)
│   ├── gemini_ai.py             # Two-tier AI client (Flash low/high thinking)
│   ├── notifier.py              # WhatsApp (CallMeBot) + Telegram messaging
│   ├── state.py                 # JSON state management (day/week transitions)
│   ├── formatter.py             # All message templates and formatting
│   ├── morning_job.py           # Morning orchestrator
│   ├── reminder_job.py          # Reminder orchestrator
│   └── autosolve_job.py         # Auto-solve orchestrator
├── prompts/
│   ├── decode_easy_medium.txt   # Easy/Medium question decode prompt
│   ├── decode_hard.txt          # Hard question decode + 5-hint generation prompt
│   ├── submission_analysis.txt  # Socratic submission analysis prompt
│   └── auto_solve.txt           # Solution + walkthrough + quiz generation prompt
├── state.json                   # Persisted state (committed by Actions)
├── requirements.txt             # Python dependencies
├── DEEP_DIVE.md                 # Comprehensive design documentation
└── README.md                    # You are here
```

---

## Setup Guide

### Prerequisites

- A **GitHub** account (free)
- A **Google AI Studio** API key ([get one free](https://aistudio.google.com/apikey))
- A **LeetCode** account (with active session cookie)
- A **Telegram Bot** ([create via BotFather](https://t.me/botfather))
- **CallMeBot** WhatsApp API ([activate here](https://www.callmebot.com/blog/free-api-whatsapp-messages/))

### Step 1: Fork & Clone

```bash
git clone https://github.com/ManveerAnand/StreakForge.git
cd StreakForge
```

### Step 2: Get Your LeetCode Cookies

1. Go to [leetcode.com](https://leetcode.com) and log in
2. Open DevTools → Application → Cookies → `https://leetcode.com`
3. Copy the values of `LEETCODE_SESSION` and `csrftoken`

> ⚠️ These cookies expire periodically. StreakForge includes a weekly health check that alerts you when they expire.

### Step 3: Configure GitHub Secrets

Go to your fork → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Description |
|--------|-------------|
| `LEETCODE_SESSION` | Your LeetCode session cookie |
| `CSRF_TOKEN` | Your LeetCode CSRF token |
| `GEMINI_API_KEY` | Google AI Studio API key (primary) |
| `GEMINI_API_KEY_2` | *(Optional)* Second Gemini API key for rotation |
| `GEMINI_API_KEY_3` | *(Optional)* Third Gemini API key for rotation |
| `CALLMEBOT_PHONE` | Your phone number (with country code, e.g. `919876543210`) |
| `CALLMEBOT_API_KEY` | CallMeBot API key (received via WhatsApp) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID ([find it here](https://t.me/userinfobot)) |

### Step 4: Enable GitHub Actions

Go to the **Actions** tab in your fork and enable workflows. The cron schedules will start running automatically.

### Step 5: Test (Optional)

Trigger any workflow manually from the Actions tab using "Run workflow".

---

## How It Works

### AI Strategy — Two Tiers, One Model

StreakForge uses **Gemini 3 Flash Preview** with dynamic thinking depth:

| Task | Thinking Level | Why |
|------|---------------|-----|
| Easy/Medium decode | `low` | Straightforward — needs speed |
| Hard decode + hint generation | `high` | Needs deep reasoning for quality 5-level hints |
| Submission analysis | `high` | Must understand code logic and edge cases |
| Solution generation | `high` | Accuracy-critical — code must pass LeetCode judge |
| Reminders & congrats | `low` | Creative text — speed over depth |

### Hard Questions Get Special Treatment

Instead of dumping all information upfront, Hard questions activate a **progressive 5-level hint system**:

1. **Pattern Recognition** — "This feels like a problem where..." (just tags/vibes)
2. **Approach Direction** — "Think about what happens when..." (strategy nudge)
3. **Key Mechanics** — Core data structure or technique needed
4. **Implementation Nudge** — How to structure the solution
5. **Near-Solution** — Everything except the code

Hints are dripped over time with each reminder, and available on-demand via Telegram.

### Submission-Aware Socratic Coaching

When you submit a wrong answer, StreakForge:
1. Detects new failing submissions since the last check
2. Pulls the failing test case, expected vs actual output, and error type
3. Feeds this to Gemini with a Socratic prompt
4. Sends an **indirect** hint — never "your code is wrong at line 5", always "people often get confused when the input has duplicates..."

### Auto-Solve Safety Net

- Activates at **11:45 PM IST** only if the question is unsolved
- **Maximum 2 per week** (any days, not necessarily consecutive)
- Generates a Python solution → submits to LeetCode → verifies acceptance
- Sends a **4-part learning package**: status → code → walkthrough → quiz
- If the first submission fails, retries once with failure context

---

## Cost

**$0.** Everything runs on free tiers:

| Service | Free Tier |
|---------|-----------|
| GitHub Actions | 2,000 min/month (public repo) |
| Gemini 3 Flash | 500 req/day |
| CallMeBot | Unlimited (fair use) |
| Telegram Bot API | Unlimited |
| LeetCode API | No official limits (be respectful) |

StreakForge uses ~10 min/day of Actions time and ~15-25 Gemini calls/day.

---

## Known Limitations

- **LeetCode cookies expire** — StreakForge alerts you, but you must manually refresh them
- **CallMeBot is one-way** — WhatsApp messages are broadcast only; interactive features (quiz buttons, on-demand hints) are Telegram-only
- **GitHub Actions cron ±5 min** — Delivery times may vary slightly
- **LeetCode API is undocumented** — May change without notice; StreakForge handles errors gracefully

---

## Documentation

See [DEEP_DIVE.md](DEEP_DIVE.md) for the comprehensive design document covering:
- UX philosophy and message design
- AI model selection and prompting strategy
- LeetCode GraphQL API reference
- State management design
- Risk analysis and mitigations
- Decision log

---

## License

MIT — use it, fork it, make it yours.

---

<div align="center">

**Built for the grind.** 🔥

*Stop breaking streaks. Start learning.*

</div>
