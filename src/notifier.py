"""
StreakForge — Notification System
Dual-channel: WhatsApp (CallMeBot) + Telegram Bot API.
WhatsApp = broadcast channel (push only).
Telegram = interactive channel (push + pull, quiz buttons, on-demand commands).
"""

import json
import logging
import urllib.parse
import requests

from src.config import (
    CALLMEBOT_URL,
    CALLMEBOT_PHONE,
    CALLMEBOT_API_KEY,
    TELEGRAM_API_URL_TEMPLATE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

logger = logging.getLogger("streakforge.notifier")


# ──────────────────── WhatsApp (CallMeBot) ────────────────────


def send_whatsapp(message: str) -> bool:
    """
    Send a WhatsApp message via CallMeBot.
    Supports WhatsApp formatting: *bold*, _italic_, ~strikethrough~, `monospace`
    Returns True on success, False on failure.
    """
    if not CALLMEBOT_PHONE or not CALLMEBOT_API_KEY:
        logger.warning(
            "WhatsApp not configured (missing CALLMEBOT_PHONE or CALLMEBOT_API_KEY)")
        return False

    encoded_msg = urllib.parse.quote(message)
    url = f"{CALLMEBOT_URL}?phone={CALLMEBOT_PHONE}&text={encoded_msg}&apikey={CALLMEBOT_API_KEY}"

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            logger.info("WhatsApp message sent successfully")
            return True
        else:
            logger.error("WhatsApp send failed: HTTP %s — %s",
                         resp.status_code, resp.text[:200])
            return False
    except Exception as e:
        logger.error("WhatsApp send error: %s", e)
        return False


# ──────────────────── Telegram ────────────────────


def _telegram_api(method: str, payload: dict) -> dict:
    """Make a Telegram Bot API call."""
    url = f"{TELEGRAM_API_URL_TEMPLATE.format(token=TELEGRAM_BOT_TOKEN)}/{method}"
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        logger.error("Telegram API error: %s", data)
    return data


def send_telegram(message: str, parse_mode: str = "Markdown") -> bool:
    """
    Send a text message via Telegram.
    Supports Markdown formatting.
    Returns True on success.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram not configured (missing BOT_TOKEN or CHAT_ID)")
        return False

    try:
        result = _telegram_api("sendMessage", {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        })
        if result.get("ok"):
            logger.info("Telegram message sent successfully")
            return True
        return False
    except Exception as e:
        logger.error("Telegram send error: %s", e)
        return False


def send_telegram_quiz(
    question: str,
    options: list[str],
    callback_prefix: str = "quiz",
) -> bool:
    """
    Send an interactive quiz via Telegram with inline keyboard buttons.
    Each button sends a callback_data like "quiz_0", "quiz_1", etc.
    Returns True on success.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return False

    keyboard = {
        "inline_keyboard": [
            [{"text": opt, "callback_data": f"{callback_prefix}_{i}"}]
            for i, opt in enumerate(options)
        ]
    }

    try:
        result = _telegram_api("sendMessage", {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": question,
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        })
        if result.get("ok"):
            logger.info("Telegram quiz sent successfully")
            return True
        return False
    except Exception as e:
        logger.error("Telegram quiz send error: %s", e)
        return False


def answer_telegram_callback(callback_query_id: str, text: str, show_alert: bool = False) -> bool:
    """
    Respond to a Telegram inline keyboard button press.
    text: feedback shown to the user (max 200 chars).
    show_alert: if True, shows a popup instead of inline notification.
    """
    try:
        result = _telegram_api("answerCallbackQuery", {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        })
        return result.get("ok", False)
    except Exception as e:
        logger.error("Telegram callback answer error: %s", e)
        return False


# ──────────────────── Unified Send ────────────────────


def notify(message: str, telegram_extra: dict | None = None) -> dict:
    """
    Send a message to both WhatsApp and Telegram.
    telegram_extra: optional dict with 'reply_markup' for inline keyboards.
    Returns {"whatsapp": bool, "telegram": bool} indicating success per channel.
    """
    wa_ok = send_whatsapp(message)

    if telegram_extra and "reply_markup" in telegram_extra:
        # Send with keyboard
        tg_ok = False
        try:
            result = _telegram_api("sendMessage", {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
                **telegram_extra,
            })
            tg_ok = result.get("ok", False)
        except Exception as e:
            logger.error("Telegram send with extras error: %s", e)
    else:
        tg_ok = send_telegram(message)

    return {"whatsapp": wa_ok, "telegram": tg_ok}


def notify_quiz(
    whatsapp_text: str,
    telegram_question: str,
    options: list[str],
    callback_prefix: str = "quiz",
) -> dict:
    """
    Send quiz to both channels.
    WhatsApp: text-based (reply A/B/C/D).
    Telegram: interactive buttons.
    """
    wa_ok = send_whatsapp(whatsapp_text)
    tg_ok = send_telegram_quiz(telegram_question, options, callback_prefix)
    return {"whatsapp": wa_ok, "telegram": tg_ok}


def send_alert(message: str) -> dict:
    """Send a high-priority alert (e.g., session expired). Same as notify but logged differently."""
    logger.warning("ALERT: %s", message)
    return notify(f"⚠️ *StreakForge Alert*\n\n{message}")
