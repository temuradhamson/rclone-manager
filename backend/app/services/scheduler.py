import asyncio
import logging
from datetime import datetime, timedelta

from croniter import croniter
from sqlalchemy import select

from app.core.database import async_session
from app.models.models import SyncTask, Schedule, TaskExecution
from app.services.sync_engine import run_task
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None


def _calc_next_run(schedule: Schedule, from_time: datetime | None = None) -> datetime:
    """Calculate next run time based on schedule type."""
    now = from_time or datetime.utcnow()
    if schedule.schedule_type == "cron" and schedule.cron_expression:
        cron = croniter(schedule.cron_expression, now)
        return cron.get_next(datetime)
    elif schedule.schedule_type == "interval" and schedule.interval_seconds:
        base = schedule.last_run_at or now
        next_run = base + timedelta(seconds=schedule.interval_seconds)
        # If next_run is in the past, advance to next future interval
        while next_run <= now:
            next_run += timedelta(seconds=schedule.interval_seconds)
        return next_run
    return now + timedelta(hours=1)


async def _is_task_running(db, task_id: int) -> bool:
    """Check if there's already a running execution for this task."""
    result = await db.execute(
        select(TaskExecution).where(
            TaskExecution.task_id == task_id,
            TaskExecution.status == "running",
        )
    )
    return result.scalar_one_or_none() is not None


async def _scheduler_loop():
    # Wait a bit for app to fully start
    await asyncio.sleep(5)
    logger.info("Scheduler loop started")

    while True:
        try:
            async with async_session() as db:
                # Get all active schedules with their tasks
                result = await db.execute(
                    select(Schedule).where(Schedule.is_active == True)
                )
                schedules = result.scalars().all()

                now = datetime.utcnow()
                for schedule in schedules:
                    # Initialize next_run_at if not set
                    if not schedule.next_run_at:
                        schedule.next_run_at = _calc_next_run(schedule)
                        await db.commit()
                        continue

                    if schedule.next_run_at <= now:
                        task = await db.get(SyncTask, schedule.task_id)
                        if not task or not task.is_enabled:
                            schedule.next_run_at = _calc_next_run(schedule)
                            await db.commit()
                            continue

                        # Skip if task is already running
                        if await _is_task_running(db, task.id):
                            logger.info(f"Task {task.id} ({task.name}) already running, skipping scheduled run")
                            schedule.next_run_at = _calc_next_run(schedule)
                            await db.commit()
                            continue

                        # Run the task
                        try:
                            logger.info(f"Scheduled run: task {task.id} ({task.name})")
                            await run_task(task, db, trigger="scheduled")
                            schedule.last_run_at = now
                        except Exception as e:
                            logger.error(f"Scheduled run failed for task {task.id}: {e}")

                        schedule.next_run_at = _calc_next_run(schedule)
                        await db.commit()

            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(10)


def start_scheduler():
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_scheduler_loop())
    logger.info("Scheduler started")


def stop_scheduler():
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
        logger.info("Scheduler stopped")
