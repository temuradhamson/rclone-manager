"""Telegram notification service for sync events."""

import asyncio
import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _format_size(bytes_val: int) -> str:
    if bytes_val <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_val)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


async def send_telegram(message: str):
    """Send message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            })
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


async def notify_sync_error(task_name: str, error: str):
    await send_telegram(
        f"🔴 <b>Sync Error</b>\n"
        f"Task: <code>{task_name}</code>\n"
        f"Error: {error[:200]}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )


async def notify_sync_complete(task_name: str, transferred: int = 0, duration: float = 0):
    await send_telegram(
        f"✅ <b>Sync Complete</b>\n"
        f"Task: <code>{task_name}</code>\n"
        f"Transferred: {_format_size(transferred)}\n"
        f"Duration: {duration:.0f}s"
    )


async def notify_conflict(task_name: str, files: list[str]):
    file_list = "\n".join(f"• {f}" for f in files[:10])
    extra = f"\n... and {len(files) - 10} more" if len(files) > 10 else ""
    await send_telegram(
        f"⚠️ <b>Bisync Conflicts</b>\n"
        f"Task: <code>{task_name}</code>\n"
        f"Files:\n{file_list}{extra}"
    )
