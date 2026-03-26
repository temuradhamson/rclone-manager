import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.models import TaskExecution
from app.services.rclone_client import rclone_client
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)

_monitor_task: asyncio.Task | None = None


async def _monitor_loop():
    while True:
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(TaskExecution).where(TaskExecution.status == "running")
                )
                running = result.scalars().all()

                if not running:
                    await asyncio.sleep(2)
                    continue

                for execution in running:
                    if not execution.rclone_job_id:
                        continue
                    try:
                        status = await rclone_client.job_status(execution.rclone_job_id)
                        finished = status.get("finished", False)
                        success = status.get("success", False)
                        error = status.get("error", "")

                        if finished:
                            execution.status = "completed" if success else "failed"
                            execution.finished_at = datetime.utcnow()
                            if execution.started_at:
                                execution.duration_seconds = (
                                    execution.finished_at - execution.started_at
                                ).total_seconds()
                            if error:
                                execution.error_message = error

                            # Get final stats
                            try:
                                stats = await rclone_client.get_stats()
                                import json
                                execution.stats_json = json.dumps(stats)
                                execution.bytes_transferred = stats.get("bytes", 0)
                                execution.files_transferred = stats.get("transfers", 0)
                                execution.files_checked = stats.get("checks", 0)
                                execution.files_deleted = stats.get("deletes", 0)
                                execution.errors_count = stats.get("errors", 0)
                            except Exception:
                                pass

                            await db.commit()
                            await ws_manager.broadcast({
                                "type": "task_completed" if success else "task_failed",
                                "task_id": execution.task_id,
                                "execution_id": execution.id,
                                "error": error or None,
                            })
                        else:
                            # Broadcast progress
                            try:
                                stats = await rclone_client.get_stats()
                                await ws_manager.broadcast({
                                    "type": "progress",
                                    "task_id": execution.task_id,
                                    "execution_id": execution.id,
                                    "data": {
                                        "bytes": stats.get("bytes", 0),
                                        "totalBytes": stats.get("totalBytes", 0),
                                        "speed": stats.get("speed", 0),
                                        "eta": stats.get("eta", 0),
                                        "percentage": (
                                            round(stats["bytes"] / stats["totalBytes"] * 100)
                                            if stats.get("totalBytes", 0) > 0 else 0
                                        ),
                                        "checks": stats.get("checks", 0),
                                        "transfers": stats.get("transfers", 0),
                                        "transferring": stats.get("transferring", []),
                                    }
                                })
                            except Exception:
                                pass

                    except Exception as e:
                        if "job not found" in str(e).lower():
                            execution.status = "failed"
                            execution.error_message = "Job disappeared from rclone"
                            execution.finished_at = datetime.utcnow()
                            await db.commit()
                            await ws_manager.broadcast({
                                "type": "task_failed",
                                "task_id": execution.task_id,
                                "execution_id": execution.id,
                                "error": "Job disappeared",
                            })

            await asyncio.sleep(1.5)

        except Exception as e:
            logger.error(f"Progress monitor error: {e}")
            await asyncio.sleep(3)


def start_monitor():
    global _monitor_task
    _monitor_task = asyncio.create_task(_monitor_loop())
    logger.info("Progress monitor started")


def stop_monitor():
    global _monitor_task
    if _monitor_task:
        _monitor_task.cancel()
        _monitor_task = None
        logger.info("Progress monitor stopped")
