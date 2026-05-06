"""
Telegram notifications. Silent no-op if credentials are not configured.
"""
from __future__ import annotations
import requests
from loguru import logger
from .config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.debug(f"[telegram-disabled] {message}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message,
                  "parse_mode": "Markdown"},
            timeout=5,
        )
    except Exception as e:
        logger.warning(f"telegram send failed: {e}")
