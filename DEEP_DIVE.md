# LeetCode Daily Challenge Automation — Deep Dive Documentation

> **Living Document** — This file is appended as the project evolves. Every design decision, research finding, and UX philosophy is captured here. Nothing is omitted.

---

## Table of Contents

1. [Project Vision & Philosophy](#1-project-vision--philosophy)
2. [Core Workflow Overview](#2-core-workflow-overview)
3. [UX Design — The Most Important Section](#3-ux-design--the-most-important-section)
   - 3.1 [Message Design Philosophy](#31-message-design-philosophy)
   - 3.2 [Easy/Medium Question Flow](#32-easymedium-question-flow)
   - 3.3 [Hard Question Flow — The Adaptive Experience](#33-hard-question-flow--the-adaptive-experience)
   - 3.4 [Submission-Aware Contextual Hinting](#34-submission-aware-contextual-hinting)
   - 3.5 [Reminder Escalation System](#35-reminder-escalation-system)
   - 3.6 [Auto-Solve Post-Solve Experience](#36-auto-solve-post-solve-experience)
   - 3.7 [Comprehension Quiz Design](#37-comprehension-quiz-design)
4. [AI Strategy — Model Selection & Prompting](#4-ai-strategy--model-selection--prompting)
   - 4.1 [Two-Tier Model Architecture](#41-two-tier-model-architecture)
   - 4.2 [Gemini Model Landscape (March 2026)](#42-gemini-model-landscape-march-2026)
   - 4.3 [Prompting Philosophy](#43-prompting-philosophy)
   - 4.4 [Prompt Templates (Detailed)](#44-prompt-templates-detailed)
5. [Technical Architecture](#5-technical-architecture)
   - 5.1 [System Architecture Overview](#51-system-architecture-overview)
   - 5.2 [Repository Structure](#52-repository-structure)
   - 5.3 [GitHub Actions Scheduling](#53-github-actions-scheduling)
   - 5.4 [State Management](#54-state-management)
6. [LeetCode API — Complete Reference](#6-leetcode-api--complete-reference)
   - 6.1 [GraphQL Endpoint & Authentication](#61-graphql-endpoint--authentication)
   - 6.2 [Fetch Daily Challenge](#62-fetch-daily-challenge)
   - 6.3 [Check Solve Status](#63-check-solve-status)
   - 6.4 [Fetch User Submissions (For Hint Analysis)](#64-fetch-user-submissions-for-hint-analysis)
   - 6.5 [Fetch Submission Details (Code, Errors, Failing Test Cases)](#65-fetch-submission-details-code-errors-failing-test-cases)
   - 6.6 [Submit a Solution](#66-submit-a-solution)
   - 6.7 [Rate Limiting & Risks](#67-rate-limiting--risks)
7. [Notification System](#7-notification-system)
   - 7.1 [WhatsApp via CallMeBot](#71-whatsapp-via-callmebot)
   - 7.2 [Telegram Bot](#72-telegram-bot)
   - 7.3 [Dual-Channel Strategy](#73-dual-channel-strategy)
8. [Secrets & Configuration](#8-secrets--configuration)
9. [Risks, Mitigations & Edge Cases](#9-risks-mitigations--edge-cases)
10. [Decision Log](#10-decision-log)
11. [Open Questions & Future Ideas](#11-open-questions--future-ideas)
12. [Changelog](#12-changelog)

---

## 1. Project Vision & Philosophy

### What This Is
An automated, AI-powered daily LeetCode companion that lives on your phone. It doesn't just remind you — it **teaches** you, **adapts** to your skill level, and **protects your streak** when life gets in the way.

### Core Principles

1. **UX is everything.** The quality of what lands on your phone is the entire point. Every message should feel like a thoughtful mentor texting you, not a bot dumping data.

2. **Never dump information.** Especially for hard problems — information is revealed progressively, step by step, at the right time.

3. **Adapt to difficulty.** Easy, Medium, and Hard questions get fundamentally different treatment. Hard questions activate the deep-reasoning AI model and an entirely different UX flow.

4. **Be Socratic, not prescriptive.** When you're struggling, the system doesn't say "you're wrong here." It says "people often get confused by this part" or "think about what happens when the input is empty." It guides without spoon-feeding.

5. **Submission-aware intelligence.** The system doesn't operate in a vacuum. It reads your actual submissions, analyzes your wrong answers, and gives hints that address YOUR specific mistakes — without explicitly calling them out.

6. **Streak protection with discipline.** Auto-solve exists to prevent demoralization from broken streaks. But it's limited (2 per week) so it can't become a crutch. And when it activates, it turns into a learning opportunity.

7. **Zero cost.** The entire system runs on free-tier services. No credit card required.

### Who This Is For
**You** — someone actively practicing DSA, doing LeetCode daily, who sometimes skips hard questions and needs a system that keeps them accountable while genuinely helping them learn.

---

## 2. Core Workflow Overview

### Daily Timeline (IST)

```
┌─────────────────────────────────────────────────────────────────┐
│  MIDNIGHT UTC (5:30 AM IST) — New daily question appears        │
│                                                                  │
│  6:00 AM IST — MORNING DELIVERY                                 │
│  ├─ Fetch daily question from LeetCode                          │
│  ├─ AI decodes the question                                     │
│  ├─ If HARD → activate Pro-tier AI, progressive hint system     │
│  ├─ Send formatted breakdown to WhatsApp + Telegram             │
│  └─ Include: tags, decoded meaning, difficulty-appropriate tips  │
│                                                                  │
│  THROUGHOUT THE DAY — SUBMISSION MONITORING (if unsolved)        │
│  ├─ Every reminder cycle: check if solved                       │
│  ├─ If wrong submissions detected: analyze code & errors        │
│  └─ Generate contextual, Socratic hints based on actual mistakes│
│                                                                  │
│  10:00 AM IST — REMINDER #1 (if unsolved)                       │
│  ├─ Casual nudge                                                │
│  └─ If HARD + has wrong submissions → contextual hint           │
│                                                                  │
│  2:00 PM IST — REMINDER #2 (if unsolved)                        │
│  ├─ Slightly more urgent                                        │
│  └─ If HARD → time-drip: approach-level hint                    │
│                                                                  │
│  6:00 PM IST — REMINDER #3 (if unsolved)                        │
│  ├─ Evening nudge with encouragement                            │
│  └─ If HARD → deeper conceptual hint                            │
│                                                                  │
│  9:00 PM IST — REMINDER #4 / FINAL WARNING (if unsolved)        │
│  ├─ "Auto-solve kicks in at 11:45 PM"                           │
│  └─ If HARD → strongest hint without giving away solution       │
│                                                                  │
│  11:45 PM IST — AUTO-SOLVE (if unsolved + quota available)      │
│  ├─ Check weekly auto-solve count (max 2/week)                  │
│  ├─ If under limit: generate solution → submit → explain → quiz │
│  └─ If over limit: "Streak is in your hands tonight"            │
│                                                                  │
│  ON-DEMAND (anytime via Telegram)                                │
│  ├─ User sends "hint" → get next progressive hint               │
│  ├─ User sends "tags" → get topic tags                          │
│  └─ User sends "status" → get today's progress summary          │
└─────────────────────────────────────────────────────────────────┘
```

### Auto-Solve Rules
- **Trigger:** 11:45 PM IST, if the daily question is unsolved
- **Limit:** Maximum **2 auto-solves per week** (any 2 days, not necessarily consecutive)
- **Weekly reset:** Every Monday at midnight IST
- **When limit exceeded:** System sends a message — "You've used both auto-solves this week. Tonight's streak depends on you." — and does NOT submit
- **Post auto-solve:** Full learning package delivered (solution + explanation + comprehension quiz)

---

## 3. UX Design — The Most Important Section

### 3.1 Message Design Philosophy

Every message that reaches the user's phone must satisfy these criteria:

1. **Scannable in 5 seconds.** The first 2-3 lines must convey the essential info. Details come after.
2. **Visually structured.** Use WhatsApp formatting (`*bold*`, `_italic_`, line breaks) and Telegram Markdown to create visual hierarchy.
3. **Emotionally calibrated.** Morning messages are energizing. Reminders escalate in urgency without being annoying. Post-solve explanations are thorough and encouraging.
4. **Contextually aware.** Messages reference the specific problem, its difficulty, its tags, and (when available) the user's own submissions.
5. **Progressive disclosure.** Especially for hard questions — never dump everything at once.

### 3.2 Easy/Medium Question Flow

For Easy and Medium questions, the user is generally capable of solving them independently. The system's role is to **inform and motivate**, not to hand-hold.

#### Morning Message (Easy/Medium) — Example Format:

```
☀️ *LeetCode Daily — March 5, 2026*

📌 *Two Sum* (Easy)
🏷️ Array, Hash Table

*What it's really asking:*
Find two numbers in an array that add up to a target. Return their indices.

*Key insight:*
You don't need to check every pair. Think about what you've already seen as you scan left to right.

*Edge cases to consider:*
• Can the same element be used twice? (No)
• Are there always exactly two valid numbers? (Yes, per constraints)

🔗 leetcode.com/problems/two-sum

💪 You've got this. Easy one today!
```

**What the AI does for Easy/Medium (Flash model, thinking=low):**
- Strips the problem statement's fluff — "decode" it into plain language
- Identifies the core algorithmic insight without giving away the solution
- Lists 2-3 edge cases
- Adds a one-line motivational nudge calibrated to difficulty

#### Reminder Messages (Easy/Medium):

| Time | Tone | Example |
|------|------|---------|
| 10:00 AM | Casual | "Hey, today's LeetCode is still waiting — *Two Sum* (Easy). Quick one! 🎯" |
| 2:00 PM | Nudge | "Afternoon check-in: *Two Sum* still unsolved. It's an Easy — won't take long! ⏰" |
| 6:00 PM | Urgent | "Evening reminder: *Two Sum* is still open. Don't let an Easy question break the streak! 🔥" |
| 9:00 PM | Final | "⚠️ Last call — *Two Sum* unsolved. Auto-solve at 11:45 PM if you don't get to it." |

### 3.3 Hard Question Flow — The Adaptive Experience

This is where the system fundamentally changes behavior. Hard questions are treated as a **learning journey**, not a task to complete.

#### Why Hard Questions Need Different Treatment

- The user has explicitly stated they often skip hard questions
- Information overload on a hard question causes paralysis
- The goal is to make the question feel **approachable**, not to solve it for the user
- The system should act as a patient tutor, revealing information layer by layer

#### Morning Message (Hard) — Example Format:

```
🔴 *LeetCode Daily — March 5, 2026*

📌 *Median of Two Sorted Arrays* (Hard)
🏷️ Array, Binary Search, Divide and Conquer

Don't be intimidated. Let's break this down.

*In plain English:*
You have two sorted lists of numbers. Find the middle value if you merged them into one sorted list.

*Why it's marked Hard:*
The naive approach (merge and find middle) is O(n+m). The challenge is doing it in O(log(min(n,m))).

*First, just think about this:*
If you had to split both arrays such that all elements on the left side are smaller than all elements on the right — how would you know you found the right split?

💡 I'll drip hints throughout the day. Or send "hint" on Telegram anytime.

🔗 leetcode.com/problems/median-of-two-sorted-arrays
```

**What's different:**
- No "key insight" that gives away the approach — instead, a **thinking prompt** (Socratic)
- Explicitly tells the user not to be intimidated
- Explains WHY it's hard (the gap between naive and optimal)
- Promises progressive hints — reduces anxiety of "I need to figure it all out now"
- Uses the deep-thinking AI model (Gemini 3 Flash with `thinking_level=high`) for the initial analysis

#### Progressive Hint System (Hard Questions)

Hints are delivered in two ways:
1. **Time-drip (automatic):** At each reminder interval, if the question is unsolved, the reminder includes a progressively deeper hint
2. **On-demand (Telegram):** User sends "hint" and gets the next hint in the sequence immediately

**Hint Progression (5 levels):**

| Level | What It Reveals | Trigger |
|-------|-----------------|---------|
| **Level 1 — Tags & Framing** | The morning message. Topic tags, plain-English translation, why it's hard, a thinking prompt. | 6:00 AM (automatic) |
| **Level 2 — Pattern Recognition** | "This is a classic binary search problem in disguise. Think about what you're binary searching FOR." | 10:00 AM (auto) or on-demand |
| **Level 3 — Approach Direction** | "Consider binary searching on the partition point of the smaller array. If you partition at index i, what does that force in the other array?" | 2:00 PM (auto) or on-demand |
| **Level 4 — Key Mechanics** | "After partitioning, check: max_left1 ≤ min_right2 AND max_left2 ≤ min_right1. If not, which direction should you move?" | 6:00 PM (auto) or on-demand |
| **Level 5 — Near-Solution Nudge** | "You're essentially binary searching i from 0 to len(smaller). Total left half size is (n+m+1)//2. j = half - i. Check the cross-boundary conditions." | 9:00 PM (auto) or on-demand |

**Critical design rules for hints:**
- **Never give the code.** Even Level 5 is conceptual, not code.
- **Each level builds on the previous.** They're not independent; they tell a story.
- **The AI generates all 5 levels at morning time** (in one API call), and they are cached/stored for drip delivery throughout the day.
- **If the user asks for a hint via Telegram**, they get the next level they haven't seen yet. The system tracks which hint level the user is at in `state.json`.

### 3.4 Submission-Aware Contextual Hinting

This is the most sophisticated UX feature. When the system detects that the user has made wrong submissions, it **analyzes the code and errors** and provides hints that address the specific mistake — **without directly telling them what's wrong**.

#### How It Works

1. At every reminder check (or more frequently via a polling mechanism), the system calls the LeetCode API to fetch the user's submissions for today's problem
2. If a new **wrong submission** is detected (Wrong Answer, TLE, Runtime Error, etc.), the system:
   - Fetches the full submission details (code, failing test case, expected vs actual output, error messages)
   - Sends the code + error context to the AI with a carefully crafted prompt
   - The AI generates a **Socratic hint** — not "your code is wrong at line 5" but rather a indirect nudge

#### Submission-Aware Hint Examples

**Wrong Answer:**
```
Your submission:       Code that uses two nested loops
Failing test case:     [large input]
Passed:                45/60 test cases
Expected:              "5"
Your output:           "3"

AI-Generated Hint (sent to user):
───────────────────
"People often run into trouble on this problem when they
don't account for negative numbers in the array. What
happens to your logic when nums[i] is negative?"
───────────────────
```

**Time Limit Exceeded:**
```
AI-Generated Hint (sent to user):
───────────────────
"Getting TLE? Your current approach might be O(n²).
The tags for this problem include 'Hash Table' — that
usually hints at a way to trade space for time. What
if you could check 'have I seen the complement?' in O(1)?"
───────────────────
```

**Runtime Error:**
```
AI-Generated Hint (sent to user):
───────────────────
"Runtime errors on this kind of problem often come from
array index issues. When your window slides, are you
sure both pointers stay within bounds for all edge cases?"
───────────────────
```

#### Key Design Principles for Submission-Aware Hints

1. **Never quote the user's code back to them.** They know what they wrote.
2. **Never say "your code has a bug" or "you made a mistake."** Instead: "People often run into trouble when..." or "A common pitfall here is..."
3. **Reference the problem's characteristics**, not the user's specific error. The hint should feel like general wisdom that happens to be exactly relevant.
4. **If TLE:** Hint at the optimal time complexity and which data structure enables it, using the problem's tags as a natural bridge.
5. **If Wrong Answer:** Identify the conceptual misunderstanding (not the code bug) and nudge toward the right mental model.
6. **If Runtime Error:** Hint at the category of error (bounds, null, overflow) without pointing at the exact line.
7. **Only send one submission-aware hint per failed submission.** Don't spam.

#### Prompt Template for Submission Analysis

```
You are a patient DSA tutor. A student is working on this LeetCode problem:

PROBLEM: {title} ({difficulty})
DESCRIPTION: {description}
TAGS: {tags}

The student submitted code that got: {status} ({totalCorrect}/{totalTestcases} passed)

Their code:
```{language}
{code}
```

Failing test case input: {lastTestcase}
Expected output: {expectedOutput}
Their output: {codeOutput}
{runtimeError if any}
{compileError if any}

Generate a SHORT hint (2-4 sentences) that helps the student realize their mistake
WITHOUT directly pointing it out. Use phrases like:
- "People often get confused when..."
- "A common pitfall with this type of problem is..."
- "Think about what happens when..."
- "The {tag} approach usually handles this by..."

RULES:
- Do NOT reference their code directly (no "your line 5" or "your variable x")
- Do NOT give the solution or corrected code
- DO reference the problem's characteristics and constraints
- DO connect the hint to the problem's tags when natural
- Keep it under 4 sentences
- Be encouraging
```

### 3.5 Reminder Escalation System

Reminders are not just "hey, solve the question." They're contextually rich and escalate appropriately.

#### Reminder Decision Tree

```
At each reminder time:
│
├─ Is the question solved? 
│  └─ YES → Send "Nice work! 🎉 {title} done." (only on first detection) → STOP
│
├─ NO → Check difficulty
│  │
│  ├─ EASY/MEDIUM
│  │  └─ Send standard reminder (tone escalates with time, see §3.2)
│  │
│  └─ HARD
│     │
│     ├─ Check for new wrong submissions since last check
│     │  ├─ YES → Analyze submission → Send submission-aware hint (§3.4)
│     │  └─ NO → Send next time-drip hint (§3.3) + reminder
│     │
│     └─ Check current hint level
│        ├─ If user has asked for hints via Telegram → they may be ahead
│        └─ Time-drip only delivers up to the level for that time slot
```

#### Reminder Tone by Time (All Difficulties)

| Time | Tone | Emotional Calibration |
|------|------|----------------------|
| 10:00 AM | Light, friendly | "No rush, just keeping you posted" |
| 2:00 PM | Encouraging | "Good time to take a crack at it" |
| 6:00 PM | Warm urgency | "Evening's here — let's keep the streak alive" |
| 9:00 PM | Serious but supportive | "Last reminder before auto-solve. You've got 2h 45m." |

### 3.6 Auto-Solve Post-Solve Experience

When the system auto-solves at 11:45 PM, the resulting message is not just a code dump. It's a **complete learning package** delivered in a structured, digestible format.

#### Auto-Solve Message Flow (Multi-Message Sequence)

**Message 1 — Status Update:**
```
✅ *Auto-Solve Activated*

I've submitted a solution for today's *{title}* ({difficulty}).

Your streak is safe. 🔥
Auto-solves used this week: {count}/2

Let me walk you through the solution. 👇
```

**Message 2 — The Solution (with context):**
```
📝 *Solution: {title}*

*Approach: {approach_name}*
*Time: O({time}) | Space: O({space})*

```python
{solution_code}
```

*Why this approach:*
{1-2 sentence justification of why this approach is optimal for this problem}
```

**Message 3 — Step-by-Step Walkthrough:**
```
🧠 *Walkthrough*

Let's trace through Example 1: {example_input}

Step 1: {what happens}
Step 2: {what happens}
Step 3: {what happens}
...
Result: {output} ✓

*The key insight:*
{The one conceptual takeaway that makes this problem "click"}
```

**Message 4 — Comprehension Quiz (Telegram only, with buttons):**
```
📋 *Quick Check — Did you get it?*

Q: {comprehension_question}

[Button A: {option_a}]
[Button B: {option_b}]
[Button C: {option_c}]
[Button D: {option_d}]
```

On WhatsApp (no buttons), the quiz is text-based:
```
📋 *Quick Check — Did you get it?*

Q: {comprehension_question}

A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Reply with A, B, C, or D
```

### 3.7 Comprehension Quiz Design

The quiz is not a formality. It's designed to verify the user **actually understood** the solution, not just read it.

#### Quiz Question Types

1. **"What if" questions:** "What would happen if the input array was empty?" — tests edge case understanding
2. **"Why" questions:** "Why do we use a hash map here instead of sorting?" — tests decision-making comprehension
3. **"What complexity" questions:** "What is the time complexity of this solution?" — tests analytical understanding
4. **"Trace" questions:** "Given input [2,7,11,15] and target 9, what is stored in the hash map after processing index 0?" — tests step-by-step comprehension

#### Quiz Generation Rules

- Always 1 question (keep it quick — it's 11:45 PM, the user is tired)
- 4 options, exactly 1 correct
- Wrong options should be **plausible** (common misconceptions, not random garbage)
- After the user answers:
  - **Correct:** "✅ Exactly right! You've got it."
  - **Wrong:** "Not quite. {1-sentence explanation of why the correct answer is right}. Try reviewing the walkthrough above."

---

## 4. AI Strategy — Model Selection & Prompting

### 4.1 Two-Tier Model Architecture

The system uses two tiers of AI, selected based on the task:

| Tier | Model | When Used | Why |
|------|-------|-----------|-----|
| **Automation Tier** | `gemini-3-flash-preview` with `thinking_level="low"` | Easy/Medium question decoding, reminder text, basic formatting | Fast, free, good enough for straightforward tasks |
| **Reasoning Tier** | `gemini-3-flash-preview` with `thinking_level="high"` | Hard question decoding, hint generation (all 5 levels), submission analysis, solution generation, quiz creation | Same model, but forced into deep reasoning mode via thinking_level. Free tier. |

#### Why Not Gemini 3.1 Pro?

- `gemini-3.1-pro-preview` has **no free tier** ($2/M input, $12/M output)
- Budget constraint: zero
- `gemini-3-flash-preview` with `thinking_level="high"` is surprisingly capable for reasoning tasks
- If the free tier ever becomes insufficient, upgrading to `gemini-2.5-pro` (free tier, stable GA) is the fallback

### 4.2 Gemini Model Landscape (March 2026)

Complete reference of all relevant models:

#### Gemini 3 Family (Cutting Edge)

| Model | Model ID | Free Tier | Cost (per 1M tokens) | Status |
|-------|----------|-----------|----------------------|--------|
| **Gemini 3.1 Pro Preview** | `gemini-3.1-pro-preview` | ❌ No | $2.00 in / $12.00 out | Active (latest Pro) |
| **Gemini 3 Flash Preview** | `gemini-3-flash-preview` | ✅ Yes | $0.50 in / $3.00 out | Active (latest Flash) |
| **Gemini 3.1 Flash-Lite Preview** | `gemini-3.1-flash-lite-preview` | ✅ Yes | $0.25 in / $1.50 out | Active (cheapest) |
| Gemini 3 Pro Preview | `gemini-3-pro-preview` | — | — | ⚠️ DEPRECATED (shutdown March 9, 2026) |

#### Gemini 2.5 Family (Stable GA — Fallback)

| Model | Model ID | Free Tier | Status |
|-------|----------|-----------|--------|
| Gemini 2.5 Pro | `gemini-2.5-pro` | ✅ Yes | Stable GA |
| Gemini 2.5 Flash | `gemini-2.5-flash` | ✅ Yes | Stable GA |
| Gemini 2.5 Flash-Lite | `gemini-2.5-flash-lite` | ✅ Yes | Stable GA |

#### Thinking / Reasoning Modes

**Gemini 3 models** use `thinkingLevel`:
| Level | Behavior |
|-------|----------|
| `minimal` | Near-zero thinking (Flash only; Pro can't disable) |
| `low` | Minimize latency. Good for simple tasks. |
| `medium` | Balanced. |
| `high` | Maximum reasoning depth. **Default (dynamic).** |

**Gemini 2.5 models** use `thinkingBudget`:
| Setting | Behavior |
|---------|----------|
| `0` | Thinking off (Flash/Flash-Lite only) |
| `1024` | Fixed budget |
| `-1` | Dynamic (default) |

#### SDK

```bash
pip install google-genai
```

The old `google-generativeai` library is **deprecated since Nov 2025**. Do not use it.

```python
from google import genai
from google.genai import types

client = genai.Client()  # uses GOOGLE_API_KEY env var

# Automation tier (low thinking):
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Decode this LeetCode problem...",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="low")
    )
)

# Reasoning tier (high thinking):
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Generate 5 progressive hints for this hard problem...",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    )
)
```

#### Context Windows
All current models: **1,048,576 input tokens**, **65,536 output tokens** — more than sufficient.

#### Free Tier Rate Limits
- Exact RPM/RPD limits are dynamic and viewable at [AI Studio Rate Limit page](https://aistudio.google.com/rate-limit) (requires login)
- For this use case (1-5 API calls per day), we are **well under any reasonable limit**
- RPD resets at midnight Pacific Time

### 4.3 Prompting Philosophy

The prompts are the soul of this project. Bad prompts = bad messages = failed UX.

**Prompting Principles:**

1. **Role definition.** Every prompt starts with a clear role: "You are a patient DSA tutor" or "You are a LeetCode question decoder."
2. **Output format specification.** Every prompt specifies the exact format of the response (WhatsApp-friendly text, JSON for quizzes, etc.).
3. **Constraint injection.** Explicit rules about what NOT to do (don't give away the solution, don't reference user's code directly, etc.).
4. **Context maximization.** Every relevant piece of information is included: problem title, description, difficulty, tags, constraints, examples, and (when available) user's submission history.
5. **Tone calibration.** The prompt specifies the emotional tone: encouraging for morning, urgent for 9 PM, supportive for post-auto-solve.

### 4.4 Prompt Templates (Detailed)

#### Prompt: Morning Question Decode (Easy/Medium)

```
ROLE: You are a LeetCode question decoder. Your job is to take a LeetCode problem
and explain it in simple, plain English so a DSA student can immediately understand
what they need to solve — without the confusing story wrapping.

PROBLEM TITLE: {title}
DIFFICULTY: {difficulty}
TAGS: {tags}
DESCRIPTION (HTML): {content}
CONSTRAINTS: {constraints}
EXAMPLES: {examples}

OUTPUT FORMAT (WhatsApp-compatible text, use *bold* and _italic_ for formatting):

1. "What it's really asking:" — 1-2 sentences, plain English, no jargon
2. "Key insight:" — ONE sentence hinting at the optimal approach without giving it away
3. "Edge cases to consider:" — 2-3 bullet points
4. A one-line motivational message appropriate for {difficulty} difficulty

RULES:
- Do NOT give the solution or approach name (no "use two pointers" or "use dynamic programming")
- DO hint at the direction of thinking
- Keep the total response under 150 words
- Make it feel like a knowledgeable friend explaining the problem, not a textbook
```

#### Prompt: Morning Question Decode (Hard) — Deep Reasoning

```
ROLE: You are a patient, world-class DSA tutor. A student is facing a Hard LeetCode
problem. Your goal is NOT to solve it for them but to make it feel approachable.

PROBLEM TITLE: {title}
DIFFICULTY: Hard
TAGS: {tags}
DESCRIPTION (HTML): {content}
CONSTRAINTS: {constraints}
EXAMPLES: {examples}

TASK: Generate TWO outputs.

OUTPUT 1 — MORNING MESSAGE (WhatsApp-compatible):
- "In plain English:" — What the problem actually asks, in the simplest possible terms
- "Why it's marked Hard:" — Explain the gap between the naive and optimal approach (without naming the optimal approach)
- "First, just think about this:" — ONE Socratic question that points toward the key insight
- End with: "I'll drip hints throughout the day. Or send 'hint' on Telegram anytime."
- Keep under 120 words. Be warm and encouraging. This student often skips Hard problems.

OUTPUT 2 — HINT SEQUENCE (JSON array of 5 strings):
Generate 5 progressive hints, each building on the previous:
- Hint 1: Pattern recognition — which algorithmic pattern this fits (without naming the solution)
- Hint 2: Approach direction — what to binary search / iterate / partition on
- Hint 3: Key mechanics — the core operation or comparison needed
- Hint 4: Implementation nudge — what data structures help, what to track
- Hint 5: Near-solution — the full conceptual algorithm in plain English (still no code)

RULES:
- Never include code in any hint
- Each hint should be 2-3 sentences max
- Hints should feel like a breadcrumb trail, not a lecture
- Use the problem's tags naturally (e.g., if tagged "Binary Search", hint 2 can say
  "This is a binary search problem in disguise — but what are you searching for?")
- Remember: this student gets intimidated by Hard problems. Be encouraging throughout.

OUTPUT FORMAT:
Return a JSON object: {
  "morning_message": "...",
  "hints": ["hint1", "hint2", "hint3", "hint4", "hint5"]
}
```

#### Prompt: Submission Analysis (Socratic Hint)

```
ROLE: You are a patient DSA tutor. A student submitted a wrong solution. Your job
is to help them realize their mistake WITHOUT directly telling them.

PROBLEM: {title} ({difficulty})
TAGS: {tags}
DESCRIPTION: {description_summary}

SUBMISSION STATUS: {status} ({totalCorrect}/{totalTestcases} passed)
LANGUAGE: {language}

STUDENT'S CODE:
```{language}
{code}
```

FAILING TEST CASE INPUT: {lastTestcase}
EXPECTED OUTPUT: {expectedOutput}
STUDENT'S OUTPUT: {codeOutput}
RUNTIME ERROR (if any): {runtimeError}
COMPILE ERROR (if any): {compileError}

TASK: Generate a short hint (2-4 sentences) that guides the student to find their
mistake without pointing it out directly.

RULES:
- Use phrases like: "People often get confused when...", "A common pitfall is...",
  "Think about what happens when...", "The {tag} pattern usually handles this by..."
- NEVER reference their code directly (no "your line 5", "your variable x", "your function")
- NEVER say "your code has a bug" or "you made a mistake"
- NEVER give the corrected code or the solution
- DO reference the problem's specific constraints or properties
- Connect the hint to the problem's tags when natural
- Be encouraging — they're trying, and that matters
- Keep it under 4 sentences

OUTPUT: The hint text only (WhatsApp-compatible formatting).
```

#### Prompt: Auto-Solve Solution Generation

```
ROLE: You are an expert competitive programmer. Generate a clean, optimal solution.

PROBLEM: {title} ({difficulty})
TAGS: {tags}
DESCRIPTION: {content}
CONSTRAINTS: {constraints}
EXAMPLES: {examples}
CODE SNIPPETS: {code_snippets_for_python3}

TASK: Generate THREE outputs.

OUTPUT 1 — SOLUTION CODE:
- Language: Python 3
- Use the provided code snippet template (class Solution, method signature)
- Clean, well-commented code
- Optimal time and space complexity

OUTPUT 2 — WALKTHROUGH:
- State the approach name and complexity: "Approach: {name}, Time: O(...), Space: O(...)"
- Trace through Example 1 step by step (show what happens at each iteration/decision)
- End with "The key insight:" — one sentence that makes the problem click

OUTPUT 3 — COMPREHENSION QUIZ:
- ONE multiple-choice question that tests understanding (not memorization)
- 4 options, exactly 1 correct
- Plausible wrong answers (common misconceptions)
- Include the correct answer index

OUTPUT FORMAT (JSON):
{
  "code": "...",
  "approach_name": "...",
  "time_complexity": "...",
  "space_complexity": "...",
  "walkthrough": "...",
  "key_insight": "...",
  "quiz": {
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_index": 0,
    "explanation": "..."
  }
}
```

---

## 5. Technical Architecture

### 5.1 System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS                             │
│                                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │ morning.yml  │  │ reminders.yml│  │ auto_solve.yml       │     │
│  │ 6:00 AM IST  │  │ 4x per day   │  │ 11:45 PM IST         │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘     │
│         │                 │                      │                  │
│         ▼                 ▼                      ▼                  │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                    Python Scripts                        │       │
│  │  morning_job.py | reminder_job.py | autosolve_job.py    │       │
│  └───────┬──────────────┬──────────────────┬───────────────┘       │
│          │              │                  │                        │
│          ▼              ▼                  ▼                        │
│  ┌──────────────┐ ┌──────────┐  ┌────────────────────┐            │
│  │ leetcode_api  │ │ gemini_ai│  │ state (state.json) │            │
│  │ .py           │ │ .py      │  │ committed to repo  │            │
│  └──────┬────────┘ └────┬─────┘  └────────┬───────────┘            │
│         │               │                 │                        │
└─────────┼───────────────┼─────────────────┼────────────────────────┘
          │               │                 │
          ▼               ▼                 │
  ┌───────────────┐ ┌──────────────┐        │
  │ LeetCode      │ │ Google       │        │
  │ GraphQL API   │ │ Gemini API   │        │
  └───────────────┘ └──────────────┘        │
                                            │
          ┌─────────────────────────────────┘
          ▼
  ┌───────────────────────────────────────────┐
  │              NOTIFICATIONS                 │
  │                                            │
  │  ┌─────────────────┐  ┌────────────────┐  │
  │  │ WhatsApp         │  │ Telegram       │  │
  │  │ (CallMeBot API)  │  │ (Bot API)      │  │
  │  └─────────────────┘  └────────────────┘  │
  │                                            │
  │         ┌───────────────────┐              │
  │         │ Telegram Webhook  │              │
  │         │ (Vercel/CF Worker)│              │
  │         │ Handles: hints,   │              │
  │         │ quiz responses    │              │
  │         └───────────────────┘              │
  └───────────────────────────────────────────┘
```

### 5.2 Repository Structure

```
LEETCODE/
├── .github/
│   └── workflows/
│       ├── morning.yml              # Cron: 00:30 UTC (6:00 AM IST)
│       ├── reminders.yml            # Cron: 04:30, 08:30, 12:30, 15:30 UTC
│       ├── auto_solve.yml           # Cron: 18:15 UTC (11:45 PM IST)
│       ├── session_health_check.yml # Weekly: Mondays, check LeetCode session
│       └── keepalive.yml            # Monthly: prevent 60-day auto-disable
│
├── src/
│   ├── leetcode_api.py              # LeetCode GraphQL client (all API calls)
│   ├── gemini_ai.py                 # Two-tier Gemini client (automation + reasoning)
│   ├── notifier.py                  # WhatsApp (CallMeBot) + Telegram message sender
│   ├── quiz.py                      # Quiz delivery + response handling
│   ├── state.py                     # State management (read/write state.json)
│   ├── formatter.py                 # Message formatting (WhatsApp + Telegram variants)
│   ├── morning_job.py               # Morning flow orchestrator
│   ├── reminder_job.py              # Reminder flow orchestrator
│   ├── autosolve_job.py             # Auto-solve flow orchestrator
│   └── config.py                    # Constants, timezone config, difficulty thresholds
│
├── telegram_webhook/                # Separate deployable (Vercel/CF Worker)
│   ├── api/
│   │   └── webhook.py               # Handles: "hint", "tags", "status", quiz callbacks
│   └── vercel.json                  # Vercel deployment config
│
├── prompts/                         # All AI prompt templates (version controlled)
│   ├── decode_easy_medium.txt
│   ├── decode_hard.txt
│   ├── submission_analysis.txt
│   ├── auto_solve.txt
│   └── quiz_generation.txt
│
├── state.json                       # Persistent state (committed by Actions)
├── keepalive.txt                    # Timestamp file for keepalive workflow
├── requirements.txt                 # Python dependencies
├── DEEP_DIVE.md                     # This document
└── README.md                        # Public-facing project documentation
```

### 5.3 GitHub Actions Scheduling

#### Why GitHub Actions?
- **Free** for public repos (2,000 minutes/month, even private repos get free minutes)
- **No server to maintain** — stateless, event-driven
- **Secret management** built in (encrypted, never exposed in logs)
- **Sufficient for this use case** — we need scheduled triggers, not a 24/7 server

#### Cron Schedule (UTC — GitHub Actions is UTC-only)

| IST Time | UTC Time | Cron Expression | Workflow | Purpose |
|----------|----------|-----------------|----------|---------|
| 6:00 AM | 00:30 | `30 0 * * *` | `morning.yml` | Fetch daily, decode, send |
| 10:00 AM | 04:30 | `30 4 * * *` | `reminders.yml` | Reminder #1 |
| 2:00 PM | 08:30 | `30 8 * * *` | `reminders.yml` | Reminder #2 |
| 6:00 PM | 12:30 | `30 12 * * *` | `reminders.yml` | Reminder #3 |
| 9:00 PM | 15:30 | `30 15 * * *` | `reminders.yml` | Reminder #4 (final warning) |
| 11:45 PM | 18:15 | `15 18 * * *` | `auto_solve.yml` | Auto-solve if unsolved |
| Monday 1:00 AM | Sun 19:30 | `30 19 * * 0` | `session_health_check.yml` | Test LeetCode session |
| 1st of month | 1st 00:00 | `0 0 1 * *` | `keepalive.yml` | Prevent auto-disable |

**Note:** All workflows also include `workflow_dispatch` trigger for manual testing.

#### IST Conversion Formula
`IST = UTC + 5:30`, so `UTC = IST - 5:30`
- 6:00 AM IST = 00:30 UTC
- 10:00 AM IST = 04:30 UTC
- 2:00 PM IST = 08:30 UTC
- 6:00 PM IST = 12:30 UTC
- 9:00 PM IST = 15:30 UTC
- 11:45 PM IST = 18:15 UTC

#### Known Limitations
- **Execution delay:** Scheduled runs can be delayed by minutes during peak GitHub load (especially on the hour). For this use case, a few minutes delay is acceptable.
- **60-day auto-disable:** Public repos auto-disable scheduled workflows after 60 days of no repository activity. Mitigated by the `keepalive.yml` workflow.
- **Default branch only:** Cron schedules only trigger on the default branch (main/master).

### 5.4 State Management

State is stored in `state.json` at the repo root and committed after each modification.

#### State Schema

```json
{
  "version": 1,
  "week_start": "2026-03-02",
  "auto_solves_this_week": 1,
  "auto_solve_dates": ["2026-03-03"],
  "today": {
    "date": "2026-03-05",
    "question_slug": "median-of-two-sorted-arrays",
    "question_title": "Median of Two Sorted Arrays",
    "difficulty": "Hard",
    "tags": ["Array", "Binary Search", "Divide and Conquer"],
    "is_solved": false,
    "morning_sent": true,
    "hints_generated": true,
    "current_hint_level": 2,
    "hints_delivered": [1, 2],
    "reminders_sent": ["10:00", "14:00"],
    "submissions_analyzed": ["submission_id_123", "submission_id_456"],
    "auto_solved": false,
    "quiz_sent": false,
    "quiz_answered": false,
    "quiz_correct": null
  },
  "session_last_verified": "2026-03-03T19:30:00Z",
  "session_healthy": true,
  "last_keepalive": "2026-03-01T00:00:00Z"
}
```

#### State Operations

| Operation | When | What Changes |
|-----------|------|-------------|
| Reset `today` | Morning job, if `today.date` ≠ current date | Fresh `today` object |
| Reset week | Morning job, if current date is Monday and `week_start` ≠ this Monday | `auto_solves_this_week = 0`, new `week_start` |
| Mark morning sent | After morning message delivered | `today.morning_sent = true` |
| Store hints | After AI generates hint sequence | `today.hints_generated = true` |
| Advance hint level | After time-drip or on-demand hint | `today.current_hint_level += 1` |
| Record submission analyzed | After submission-aware hint sent | Add submission ID to `today.submissions_analyzed` |
| Mark solved | When LeetCode API confirms accepted | `today.is_solved = true` |
| Mark auto-solved | After auto-submit | `today.auto_solved = true`, increment `auto_solves_this_week` |

#### Git Commit Strategy

After modifying state, the GitHub Action runs:
```bash
git config user.name "LeetCode Bot"
git config user.email "bot@leetcode-daily.dev"
git add state.json
git diff --quiet --cached || git commit -m "state: update {date} {event}" && git push
```

The `git diff --quiet --cached ||` ensures we only commit when state actually changed.

---

## 6. LeetCode API — Complete Reference

### 6.1 GraphQL Endpoint & Authentication

**Endpoint:** `POST https://leetcode.com/graphql`

**Required Headers:**
```
Content-Type: application/json
Referer: https://leetcode.com
Cookie: LEETCODE_SESSION={session}; csrftoken={csrf}
X-CSRFToken: {csrf}
```

**How to get cookies:**
1. Log into LeetCode in your browser
2. Open DevTools → Application → Cookies → `https://leetcode.com`
3. Copy `LEETCODE_SESSION` and `csrftoken` values
4. Store in GitHub Secrets as `LEETCODE_SESSION` and `CSRF_TOKEN`

**Cookie lifespan:** Varies, typically valid for 2-6 weeks. The system includes a weekly health check that alerts you when renewal is needed.

### 6.2 Fetch Daily Challenge

**No authentication required.**

```graphql
query {
    activeDailyCodingChallengeQuestion {
        date
        link
        question {
            questionId
            questionFrontendId
            title
            titleSlug
            content
            difficulty
            topicTags {
                name
                slug
            }
            codeSnippets {
                lang
                langSlug
                code
            }
            stats
            hints
            status
            sampleTestCase
            exampleTestcases
        }
    }
}
```

**Response fields used by the system:**
| Field | Usage |
|-------|-------|
| `title` | Display in messages |
| `titleSlug` | Used for submission checks and problem URL |
| `content` | HTML of the problem — sent to AI for decoding |
| `difficulty` | Determines Easy/Medium vs Hard flow |
| `topicTags` | Tags displayed in messages, used for AI hints |
| `codeSnippets` | Python3 snippet used for auto-solve submission |
| `hints` | LeetCode's own hints — can be included in later hint levels |
| `status` | Whether the authenticated user has solved it (if authed) |
| `exampleTestcases` | Used for walkthroughs |

### 6.3 Check Solve Status

**Authentication required.**

Two approaches:

**Approach A — Via daily challenge query:** Include `status` field in the daily challenge query (see above). Returns `"ac"` if accepted, `null` if not attempted, or `"notac"` if attempted but not accepted.

**Approach B — Via submission list:** Fetch submissions for the slug and check if any have `statusDisplay == "Accepted"` with a timestamp from today.

The system uses **Approach B** as the primary method (since we also want submission details for hint analysis), with Approach A as a quick fallback.

### 6.4 Fetch User Submissions (For Hint Analysis)

**Authentication required.**

```graphql
query submissionList($offset: Int!, $limit: Int!, $slug: String) {
    submissionList(offset: $offset, limit: $limit, questionSlug: $slug) {
        hasNext
        submissions {
            id
            lang
            time
            timestamp
            statusDisplay
            runtime
            url
            isPending
            title
            titleSlug
            memory
        }
    }
}
```

**Variables:** `{ "offset": 0, "limit": 20, "slug": "two-sum" }`

**Returns** the authenticated user's submissions for that slug, newest first.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Submission ID (use for detail fetch) |
| `statusDisplay` | String | `"Accepted"`, `"Wrong Answer"`, `"Time Limit Exceeded"`, `"Memory Limit Exceeded"`, `"Runtime Error"`, `"Compile Error"`, `"Output Limit Exceeded"` |
| `timestamp` | String | Unix timestamp (seconds) |
| `lang` | String | Language slug (e.g., `"python3"`) |
| `runtime` | String | Runtime (e.g., `"4 ms"`) |
| `memory` | String | Memory (e.g., `"16.2 MB"`) |
| `isPending` | String | Whether still being judged |

### 6.5 Fetch Submission Details (Code, Errors, Failing Test Cases)

**Authentication required.**

```graphql
query submissionDetails($id: Int!) {
    submissionDetails(submissionId: $id) {
        id
        code
        statusCode
        runtimeDisplay
        runtimePercentile
        memoryDisplay
        memoryPercentile
        timestamp
        lang {
            name
            verboseName
        }
        runtimeError
        compileError
        lastTestcase
        expectedOutput
        codeOutput
        totalCorrect
        totalTestcases
        fullCodeOutput
        stdOutput
    }
}
```

**Variables:** `{ "id": 123456789 }`

**Critical fields for submission analysis:**

| Field | Description | Used For |
|-------|-------------|----------|
| `code` | Full submitted source code | AI analysis of approach and mistakes |
| `lastTestcase` | Input of the failing test case | Understanding what tripped the student |
| `expectedOutput` | Correct answer for the failing case | Comparison for AI analysis |
| `codeOutput` | Student's answer for the failing case | Identifying what went wrong |
| `runtimeError` | Error message (if RE) | AI can hint at the error category |
| `compileError` | Error message (if CE) | AI can hint at syntax issues |
| `totalCorrect` / `totalTestcases` | Pass rate | "45/60 passed" helps gauge how close they are |

### 6.6 Submit a Solution

**Authentication required.** This is used only by the auto-solve feature.

**Endpoint:** `POST https://leetcode.com/problems/{titleSlug}/submit/`

**Headers:**
```
Content-Type: application/json
Referer: https://leetcode.com/problems/{titleSlug}/
Cookie: LEETCODE_SESSION={session}; csrftoken={csrf}
X-CSRFToken: {csrf}
```

**Body:**
```json
{
    "lang": "python3",
    "question_id": "{questionId}",
    "typed_code": "{solution_code}"
}
```

**Response:** Returns a submission ID. The submission is judged asynchronously — poll for result:

**Check submission result:** `GET https://leetcode.com/submissions/detail/{submission_id}/check/`

Poll every 1-2 seconds until `state` is not `"PENDING"`. Response includes:
- `status_display`: `"Accepted"`, `"Wrong Answer"`, etc.
- `status_code`: numeric
- `runtime`: e.g., `"4 ms"`
- `memory`: e.g., `"16.2 MB"`

### 6.7 Rate Limiting & Risks

| Concern | Details |
|---------|---------|
| **Rate limits** | Undocumented. Community experience: ~2-3 req/sec is safe. Our usage (~2-5 calls/check, a few times/day) is extremely low. |
| **Recommended delays** | 1 second between consecutive API calls (e.g., between `submissionList` and `submissionDetails`). |
| **Error handling** | Implement exponential backoff on 429 (rate limit) and 403 (auth/ban). |
| **Session expiry** | `LEETCODE_SESSION` expires periodically. Weekly health check workflow detects this and alerts user. |
| **API changes** | Unofficial API — can break without notice. Abstract all GraphQL queries into `leetcode_api.py` for easy patching. |
| **IP blocking** | Extremely unlikely at our volume. GitHub Actions IPs are shared but well-known; LeetCode tolerates them. |

---

## 7. Notification System

### 7.1 WhatsApp via CallMeBot

#### Setup (One-Time)
1. Add `+34 644 66 32 62` to your phone contacts
2. Send `I allow callmebot to send me messages` via WhatsApp to that number
3. Receive an API key in the reply
4. Store phone number and API key in GitHub Secrets

#### Sending Messages

```
GET https://api.callmebot.com/whatsapp.php?phone={phone}&text={url_encoded_message}&apikey={key}
```

- Message must be URL-encoded (`%20` for spaces, `%0A` for newlines)
- Supports WhatsApp text formatting: `*bold*`, `_italic_`, `~strikethrough~`, ``` `monospace` ```
- Maximum message length: not officially documented, but ~4000 chars works reliably

#### Limitations
| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Plain text only (no buttons, no images) | Can't do interactive quizzes | Telegram handles quizzes |
| Third-party free service, no SLA | Could go down | Telegram as reliable backup |
| Single recipient only | Only you receive messages | Fine for personal use |
| Rate limits unknown | Could be throttled | We send max ~6 messages/day |
| No read receipts | Can't confirm delivery | Telegram as verification |

### 7.2 Telegram Bot

#### Setup (One-Time)
1. Search `@BotFather` on Telegram, send `/newbot`
2. Choose a name and username → receive bot token
3. Message your bot directly (any message)
4. Call `https://api.telegram.org/bot{token}/getUpdates` to find your `chat_id`
5. Store bot token and chat ID in GitHub Secrets

#### Sending Messages

```python
import requests

def send_telegram(token, chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    return requests.post(url, json=payload)
```

#### Inline Keyboards (For Quizzes)

```python
reply_markup = {
    "inline_keyboard": [
        [{"text": "A) O(n log n)", "callback_data": "quiz_0"}],
        [{"text": "B) O(n)", "callback_data": "quiz_1"}],
        [{"text": "C) O(n²)", "callback_data": "quiz_2"}],
        [{"text": "D) O(log n)", "callback_data": "quiz_3"}],
    ]
}
```

#### Handling Callbacks (Webhook)

When a user clicks a quiz button, Telegram sends a `CallbackQuery` to the webhook URL. The webhook:
1. Reads `callback_data` (e.g., `"quiz_1"`)
2. Compares to correct answer index
3. Calls `answerCallbackQuery` with feedback text
4. Optionally edits the original message to show the result

**Webhook deployment:** Vercel serverless function (free tier: 100GB-hours/month, more than enough).

#### On-Demand Commands

The Telegram webhook also handles user-initiated commands:

| Command | Action |
|---------|--------|
| `hint` or `/hint` | Deliver next progressive hint (advance hint level in state) |
| `tags` or `/tags` | Show today's question tags |
| `status` or `/status` | Show today's progress (solved?, hints used, reminders sent) |
| Quiz button click | Process answer, give feedback |

### 7.3 Dual-Channel Strategy

| Content Type | WhatsApp | Telegram |
|-------------|----------|----------|
| Morning question decode | ✅ Full message | ✅ Full message |
| Reminders | ✅ Full message | ✅ Full message |
| Progressive hints (automatic) | ✅ As part of reminder | ✅ As part of reminder |
| Submission-aware hints | ✅ Text hint | ✅ Text hint |
| Auto-solve: status | ✅ | ✅ |
| Auto-solve: solution | ✅ Code as text | ✅ Code block formatting |
| Auto-solve: walkthrough | ✅ | ✅ |
| Comprehension quiz | ✅ Text-based (reply A/B/C/D) | ✅ Interactive buttons |
| On-demand hints | ❌ (no input mechanism) | ✅ User sends "hint" |
| On-demand status | ❌ | ✅ User sends "status" |
| Quiz feedback | ❌ | ✅ Immediate inline feedback |

**WhatsApp** = broadcast channel (everything pushed to you, no interaction)
**Telegram** = interactive channel (push + pull, commands, quiz buttons)

---

## 8. Secrets & Configuration

### GitHub Secrets Required

| Secret Name | Description | How to Obtain | Renewal |
|-------------|------------|---------------|---------|
| `LEETCODE_SESSION` | LeetCode session cookie | Browser DevTools → Cookies | Every 2-6 weeks |
| `CSRF_TOKEN` | LeetCode CSRF token | Browser DevTools → Cookies | Same as above |
| `GEMINI_API_KEY` | Google AI Studio API key | aistudio.google.com → API keys | Doesn't expire |
| `CALLMEBOT_PHONE` | Your phone number (with country code) | Your phone | Never |
| `CALLMEBOT_API_KEY` | CallMeBot API key | Sent via WhatsApp after registration | Never (unless re-registered) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | @BotFather | Never (unless revoked) |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | `getUpdates` API call | Never |

### Configuration Constants (in `config.py`)

```python
TIMEZONE = "Asia/Kolkata"  # IST
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_SUBMIT_URL = "https://leetcode.com/problems/{slug}/submit/"
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}"
GEMINI_MODEL_AUTOMATION = "gemini-3-flash-preview"
GEMINI_MODEL_REASONING = "gemini-3-flash-preview"  # Same model, different thinking_level
GEMINI_THINKING_LOW = "low"
GEMINI_THINKING_HIGH = "high"
MAX_AUTO_SOLVES_PER_WEEK = 2
SOLUTION_LANGUAGE = "python3"
REMINDER_TIMES_IST = ["10:00", "14:00", "18:00", "21:00"]
AUTO_SOLVE_TIME_IST = "23:45"
MORNING_TIME_IST = "06:00"
```

---

## 9. Risks, Mitigations & Edge Cases

### Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **LeetCode session expires** | High (every 2-6 weeks) | All LeetCode features break | Weekly health check + WhatsApp/Telegram alert |
| **CallMeBot goes down** | Medium | No WhatsApp messages | Telegram as reliable backup; email as tertiary option |
| **LeetCode changes GraphQL API** | Low-Medium | API calls fail | Abstract layer in `leetcode_api.py`; monitor community repos |
| **GitHub Actions delayed** | Medium (minutes) | Late notifications | Acceptable for this use case |
| **Gemini API rate limited** | Very Low | AI features fail | 1-5 calls/day is well under limits |
| **Gemini model deprecated** | Low | Need to update model ID | Use stable model IDs; config is centralized |
| **Auto-solve generates wrong code** | Low-Medium | Solution rejected by LeetCode | Retry with different approach; fallback to brute force |

### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| **Daily question hasn't changed yet at 6 AM** | LeetCode resets at midnight UTC (5:30 AM IST). By 6:00 AM IST, the new question is always available. If not, retry after 5 minutes. |
| **User solves the question before morning message** | Morning job checks status first. If already solved, send a congratulatory message instead. |
| **Multiple wrong submissions between reminders** | Only analyze the MOST RECENT wrong submission. Track analyzed submission IDs to avoid duplicate hints. |
| **User solves the question mid-day** | The first reminder check that detects acceptance sends a "Well done!" message. All subsequent reminders skip. |
| **Weekend/holiday — user might not be coding** | System runs every day without exception. Streaks don't take days off. |
| **Contest day — daily question might be different** | LeetCode daily is independent of contests. No special handling needed. |
| **Auto-solve quota used up + question unsolved at 11:45 PM** | Send a clear message: "You've used both auto-solves this week. Tonight's streak depends on you." |
| **Telegram webhook down** | On-demand features (hint, status) won't work. Automatic features unaffected (they push, don't require webhook). |
| **State.json merge conflict** | Extremely unlikely (only bot commits). If it happens, the workflow fails; next run reads last committed state. |
| **LeetCode premium-only question** | Daily challenges are always free. No premium-gating concern. |

---

## 10. Decision Log

All major decisions, when they were made, and why.

| # | Date | Decision | Alternatives Considered | Rationale |
|---|------|----------|------------------------|-----------|
| 1 | 2026-03-05 | **Python** as primary language | Node.js, Go | Best LeetCode API libraries, fastest to build, user preference |
| 2 | 2026-03-05 | **GitHub Actions** for hosting | Railway, Render, AWS Lambda, Raspberry Pi | Free, no server maintenance, sufficient for scheduled tasks |
| 3 | 2026-03-05 | **Both WhatsApp + Telegram** for notifications | WhatsApp only, Telegram only, Email | WhatsApp for primary reach (user's main app), Telegram for interactive features (quizzes, on-demand hints) |
| 4 | 2026-03-05 | **CallMeBot** for WhatsApp | Twilio, Green API | Only viable free option; Twilio sandbox has limitations |
| 5 | 2026-03-05 | **IST timezone** (UTC+5:30) | — | User is in India |
| 6 | 2026-03-05 | **2 auto-solves per week** (any days) | 2 consecutive days, unlimited, none | Flexible enough to help when needed, strict enough to prevent dependency |
| 7 | 2026-03-05 | **Browser cookies** for LeetCode auth | Username/password, OAuth | Only reliable method; LeetCode has no official API |
| 8 | 2026-03-05 | **Gemini 3 Flash** (`thinking_level=high`) as reasoning model | Gemini 3.1 Pro (paid), Gemini 2.5 Pro (free) | Zero budget; Flash with high thinking is surprisingly capable; same model simplifies codebase |
| 9 | 2026-03-05 | **State in JSON committed to repo** | GitHub Cache, SQLite, external DB | Simplest, free, persistent, version-controlled |
| 10 | 2026-03-05 | **Socratic submission-aware hints** | Direct error messages, code diff analysis | Better pedagogically; doesn't demoralize; builds problem-solving skills |
| 11 | 2026-03-05 | **Two-tier AI** (same model, different thinking levels) | Two different models, single tier | Cost-effective, simpler config, Flash with thinking=high is sufficient |
| 12 | 2026-03-05 | **Hard questions get completely different UX** | Same flow for all difficulties | User skips hard questions; progressive disclosure & deep analysis needed |
| 13 | 2026-03-05 | **Prompts stored as separate files** in `prompts/` dir | Inline in Python code | Easier to iterate, version control changes, review independently |

---

## 11. Open Questions & Future Ideas

### Open Questions (To Be Resolved)

1. **Telegram webhook hosting:** Vercel free tier vs Cloudflare Workers vs a simple GitHub Actions polling approach? Need to decide before implementing the on-demand hint feature.

2. **What happens when auto-solve produces a wrong solution?** Should we retry with a different prompt/approach, or accept the failure and tell the user?

3. **Should we track problem-solving stats over time?** (e.g., "You've solved 23/30 days this month, 15 Easy, 10 Medium, 5 Hard"). Could be a weekly summary message.

4. **Should the system learn from which hints the user needed?** Over time, if the user always needs hints for Binary Search problems, the morning message could include extra guidance for those tags preemptively.

5. **WhatsApp quiz fallback:** How to handle quiz responses on WhatsApp, given that CallMeBot is one-way? Options: accept that quizzes are Telegram-only, or build a WhatsApp Business API integration later.

### Future Ideas (Post-MVP)

- **Daily difficulty prediction:** Based on the user's history, predict whether today's question will be challenging and adjust morning message accordingly
- **Weekly review message:** Sunday evening summary of the week — what was solved, what was auto-solved, what patterns appeared
- **Spaced repetition:** For auto-solved questions, schedule a re-visit after 3, 7, and 30 days
- **Community features:** If other people use this, anonymous aggregated stats ("72% of users found today's question hard")
- **Voice notes:** Use Gemini's audio capabilities to send voice explanations (Telegram supports voice messages)
- **Multiple language support:** Currently Python-only for auto-solve. Could support C++, Java, etc.
- **LeetCode contest reminders:** Remind about upcoming weekly/biweekly contests
- **Email digest:** Daily email with all the day's messages compiled (for users who prefer email)

---

## 12. Changelog

| Date | Section | Change |
|------|---------|--------|
| 2026-03-05 | All | Initial deep dive document created. Covers full project vision, UX design, AI strategy, technical architecture, LeetCode API reference, notification system, state management, risks, and decision log. |

---

*This is a living document. It will be updated as the project evolves.*
