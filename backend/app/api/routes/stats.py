"""Traffic stats and history API."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import DailyStats, TaskExecution

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/daily")
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    remote: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get daily transfer stats for charting."""
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = select(DailyStats).where(DailyStats.date >= since)
    if remote:
        query = query.where(DailyStats.remote_name == remote)
    query = query.order_by(DailyStats.date)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        {
            "date": r.date,
            "remote": r.remote_name,
            "uploaded": r.bytes_uploaded,
            "downloaded": r.bytes_downloaded,
            "files": r.files_transferred,
            "syncs": r.sync_count,
            "errors": r.errors_count,
        }
        for r in rows
    ]


@router.get("/summary")
async def get_summary(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated summary for dashboard."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.sum(TaskExecution.bytes_transferred).label("total_bytes"),
            func.sum(TaskExecution.files_transferred).label("total_files"),
            func.count(TaskExecution.id).label("total_syncs"),
            func.sum(TaskExecution.errors_count).label("total_errors"),
        ).where(
            TaskExecution.started_at >= since,
            TaskExecution.status == "completed",
        )
    )
    row = result.one()
    return {
        "period_days": days,
        "total_bytes": row.total_bytes or 0,
        "total_files": row.total_files or 0,
        "total_syncs": row.total_syncs or 0,
        "total_errors": row.total_errors or 0,
    }
