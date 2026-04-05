"""Notification settings API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import NotificationSettings
from app.services.notifier import send_telegram

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationSettingsUpdate(BaseModel):
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    notify_on_error: bool = True
    notify_on_complete: bool = False
    notify_on_conflict: bool = True


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        return {
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "notify_on_error": True,
            "notify_on_complete": False,
            "notify_on_conflict": True,
        }
    return {
        "telegram_bot_token": settings.telegram_bot_token or "",
        "telegram_chat_id": settings.telegram_chat_id or "",
        "notify_on_error": settings.notify_on_error,
        "notify_on_complete": settings.notify_on_complete,
        "notify_on_conflict": settings.notify_on_conflict,
    }


@router.put("/settings")
async def update_settings(data: NotificationSettingsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = NotificationSettings()
        db.add(settings)

    settings.telegram_bot_token = data.telegram_bot_token
    settings.telegram_chat_id = data.telegram_chat_id
    settings.notify_on_error = data.notify_on_error
    settings.notify_on_complete = data.notify_on_complete
    settings.notify_on_conflict = data.notify_on_conflict
    await db.commit()

    # Update runtime env for notifier
    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = data.telegram_bot_token or ""
    os.environ["TELEGRAM_CHAT_ID"] = data.telegram_chat_id or ""

    return {"ok": True}


@router.post("/test")
async def test_notification(db: AsyncSession = Depends(get_db)):
    """Send a test Telegram message."""
    result = await db.execute(select(NotificationSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings or not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"ok": False, "error": "Telegram not configured"}

    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = settings.telegram_bot_token
    os.environ["TELEGRAM_CHAT_ID"] = settings.telegram_chat_id

    await send_telegram("🔔 <b>Test notification</b>\nRclone Manager is connected!")
    return {"ok": True}
