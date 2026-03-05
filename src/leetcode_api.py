"""
StreakForge — LeetCode GraphQL API Client
Handles all communication with LeetCode's undocumented GraphQL endpoint.
"""

import time
import logging
import requests
from html import unescape
from typing import Optional

from src.config import (
    LEETCODE_GRAPHQL_URL,
    LEETCODE_SUBMIT_URL_TEMPLATE,
    LEETCODE_CHECK_URL_TEMPLATE,
    LEETCODE_SESSION,
    CSRF_TOKEN,
    API_CALL_DELAY,
    SUBMISSION_POLL_INTERVAL,
    SUBMISSION_POLL_MAX_RETRIES,
)

logger = logging.getLogger("streakforge.leetcode")


# ──────────────────── Helpers ────────────────────


def _headers(authenticated: bool = False) -> dict:
    """Build request headers. Auth headers included when needed."""
    h = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
    }
    if authenticated:
        h["Cookie"] = f"LEETCODE_SESSION={LEETCODE_SESSION}; csrftoken={CSRF_TOKEN}"
        h["X-CSRFToken"] = CSRF_TOKEN
    return h


def _graphql(query: str, variables: Optional[dict] = None, authenticated: bool = False) -> dict:
    """Execute a GraphQL query against LeetCode."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(
        LEETCODE_GRAPHQL_URL,
        json=payload,
        headers=_headers(authenticated),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        logger.error("GraphQL errors: %s", data["errors"])
        raise RuntimeError(f"LeetCode GraphQL error: {data['errors']}")

    return data["data"]


# ──────────────────── Public API ────────────────────


def get_daily_challenge() -> dict:
    """
    Fetch today's daily coding challenge.
    Returns a dict with keys:
        date, link, questionId, questionFrontendId, title, titleSlug,
        content (HTML), difficulty, topicTags (list of names),
        codeSnippets (list), hints (list), status, exampleTestcases
    No authentication required.
    """
    query = """
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
                topicTags { name slug }
                codeSnippets { lang langSlug code }
                stats
                hints
                status
                sampleTestCase
                exampleTestcases
            }
        }
    }
    """
    raw = _graphql(query)["activeDailyCodingChallengeQuestion"]
    q = raw["question"]

    return {
        "date": raw["date"],
        "link": f"https://leetcode.com{raw['link']}",
        "questionId": q["questionId"],
        "questionFrontendId": q["questionFrontendId"],
        "title": q["title"],
        "titleSlug": q["titleSlug"],
        "content": q["content"],                                   # HTML
        # Easy | Medium | Hard
        "difficulty": q["difficulty"],
        "topicTags": [t["name"] for t in (q["topicTags"] or [])],
        "codeSnippets": q["codeSnippets"] or [],
        "hints": q["hints"] or [],
        # "ac" | "notac" | None
        "status": q["status"],
        "exampleTestcases": q["exampleTestcases"] or "",
        "sampleTestCase": q.get("sampleTestCase", ""),
    }


def is_question_solved(title_slug: str) -> bool:
    """
    Check if the authenticated user has an Accepted submission for the given problem.
    Uses submissionList filtered by slug and checks for Accepted status.
    """
    subs = get_submissions(title_slug, limit=5)
    return any(s["statusDisplay"] == "Accepted" for s in subs)


def get_submissions(title_slug: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """
    Fetch the authenticated user's submissions for a specific problem.
    Returns a list of submission summary dicts.
    """
    query = """
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
    """
    variables = {"offset": offset, "limit": limit, "slug": title_slug}
    data = _graphql(query, variables, authenticated=True)
    return data["submissionList"]["submissions"] or []


def get_submission_detail(submission_id: int) -> dict:
    """
    Fetch full details for a specific submission.
    Returns code, failing test case, expected/actual output, errors, etc.
    """
    query = """
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
            lang { name verboseName }
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
    """
    time.sleep(API_CALL_DELAY)  # Rate-limiting courtesy
    data = _graphql(query, {"id": submission_id}, authenticated=True)
    return data["submissionDetails"]


def get_wrong_submissions_today(title_slug: str, today_timestamp: int) -> list[dict]:
    """
    Get all wrong (non-Accepted) submissions for a problem made today.
    today_timestamp: Unix timestamp for the start of today (midnight IST).
    Returns list of submission summaries, newest first.
    """
    subs = get_submissions(title_slug, limit=20)
    wrong = []
    for s in subs:
        ts = int(s["timestamp"])
        if ts < today_timestamp:
            break  # Submissions are newest-first; stop when we pass today
        if s["statusDisplay"] != "Accepted" and s["statusDisplay"] != "":
            wrong.append(s)
    return wrong


def submit_solution(title_slug: str, question_id: str, code: str, lang: str = "python3") -> dict:
    """
    Submit a solution to LeetCode.
    Returns the final judge result dict with status_display, runtime, memory, etc.
    """
    submit_url = LEETCODE_SUBMIT_URL_TEMPLATE.format(slug=title_slug)
    headers = _headers(authenticated=True)
    headers["Referer"] = f"https://leetcode.com/problems/{title_slug}/"

    body = {
        "lang": lang,
        "question_id": question_id,
        "typed_code": code,
    }

    resp = requests.post(submit_url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    submission_id = resp.json().get("submission_id")

    if not submission_id:
        raise RuntimeError(
            f"Submit failed — no submission_id in response: {resp.json()}")

    logger.info(
        "Solution submitted. submission_id=%s. Polling for result...", submission_id)

    # Poll for judge result
    check_url = LEETCODE_CHECK_URL_TEMPLATE.format(id=submission_id)
    for attempt in range(SUBMISSION_POLL_MAX_RETRIES):
        time.sleep(SUBMISSION_POLL_INTERVAL)
        check_resp = requests.get(
            check_url, headers=_headers(authenticated=True), timeout=15)
        check_resp.raise_for_status()
        result = check_resp.json()

        state = result.get("state")
        if state == "SUCCESS":
            logger.info(
                "Judge complete: %s (runtime=%s, memory=%s)",
                result.get("status_display", "?"),
                result.get("status_runtime", "?"),
                result.get("status_memory", "?"),
            )
            return {
                "submission_id": submission_id,
                "status_display": result.get("status_display", "Unknown"),
                "status_code": result.get("status_code"),
                "runtime": result.get("status_runtime", ""),
                "memory": result.get("status_memory", ""),
                "total_correct": result.get("total_correct"),
                "total_testcases": result.get("total_testcases"),
                "passed": result.get("status_display") == "Accepted",
            }
        elif state == "PENDING" or state == "STARTED":
            continue
        else:
            # Unexpected state
            logger.warning(
                "Unexpected judge state: %s — result: %s", state, result)
            return {
                "submission_id": submission_id,
                "status_display": result.get("status_display", state),
                "passed": False,
            }

    raise TimeoutError(
        f"Judge did not return within {SUBMISSION_POLL_MAX_RETRIES * SUBMISSION_POLL_INTERVAL}s")


def verify_session() -> bool:
    """
    Verify that the LeetCode session cookie is still valid.
    Makes a lightweight authenticated query.
    Returns True if the session is healthy.
    """
    try:
        query = """
        query {
            userStatus {
                isSignedIn
                username
            }
        }
        """
        data = _graphql(query, authenticated=True)
        signed_in = data.get("userStatus", {}).get("isSignedIn", False)
        username = data.get("userStatus", {}).get("username", "")
        if signed_in:
            logger.info("Session valid for user: %s", username)
        else:
            logger.warning("Session cookie present but user is not signed in")
        return signed_in
    except Exception as e:
        logger.error("Session verification failed: %s", e)
        return False


def get_python3_snippet(code_snippets: list[dict]) -> str:
    """Extract the Python3 code snippet from the list of code snippets."""
    for snippet in code_snippets:
        if snippet.get("langSlug") == "python3":
            return snippet["code"]
    # Fallback: try python
    for snippet in code_snippets:
        if snippet.get("langSlug") == "python":
            return snippet["code"]
    return ""
