import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import SyncTask, FileRule, TaskExecution
from app.services.rclone_client import rclone_client
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


def build_flags_from_rules(rules: list[FileRule]) -> dict:
    flags = {}
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    for rule in sorted_rules:
        if rule.action == "backup" and rule.backup_dir:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_path = f"{rule.backup_dir}/{timestamp}"
            _ensure_local_dir(backup_path)
            flags["backupDir"] = backup_path
            if rule.rule_type == "on_modify":
                flags["suffix"] = ".bak"
        elif rule.action == "move_to_trash" and rule.trash_dir:
            _ensure_local_dir(rule.trash_dir)
            flags["backupDir"] = rule.trash_dir
        elif rule.action == "skip":
            flags["immutable"] = True
        # delete_immediate — default rclone behavior, no extra flags

    return flags


def _ensure_local_dir(path: str):
    """Create local directory if it doesn't exist and path looks local."""
    if ":" in path and not path[1] == ":":
        return  # remote path like onedrive:something, skip
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create directory {path}: {e}")


async def run_task(task: SyncTask, db: AsyncSession, trigger: str = "manual") -> TaskExecution:
    execution = TaskExecution(
        task_id=task.id,
        status="running",
        trigger=trigger,
        started_at=datetime.utcnow(),
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    await ws_manager.broadcast({
        "type": "task_started",
        "task_id": task.id,
        "execution_id": execution.id,
        "task_name": task.name,
    })

    try:
        # Build flags from rules
        rules = (await db.execute(
            select(FileRule).where(FileRule.task_id == task.id)
        )).scalars().all()
        extra_flags = build_flags_from_rules(list(rules))

        # bisync doesn't support --backup-dir across different remotes
        if task.sync_mode == "bisync":
            extra_flags.pop("backupDir", None)

        # Parse extra_flags from task config
        if task.extra_flags:
            try:
                task_flags = json.loads(task.extra_flags)
                if isinstance(task_flags, dict):
                    extra_flags.update(task_flags)
            except json.JSONDecodeError:
                pass

        # Determine source and destination (normalize backslashes for rclone)
        src = task.src_path.replace("\\", "/")
        dst = task.dst_path.replace("\\", "/")
        if task.src_type == "local":
            src = src.rstrip("/") + "/"
        if task.dst_type == "local":
            dst = dst.rstrip("/") + "/"

        job_id = None
        if task.sync_mode == "copy_to_local":
            job_id = await rclone_client.start_copy(src, dst, extra_flags=extra_flags)
        elif task.sync_mode == "copy_to_remote":
            job_id = await rclone_client.start_copy(src, dst, extra_flags=extra_flags)
        elif task.sync_mode == "sync_to_local":
            job_id = await rclone_client.start_sync(src, dst, extra_flags=extra_flags)
        elif task.sync_mode == "sync_to_remote":
            job_id = await rclone_client.start_sync(src, dst, extra_flags=extra_flags)
        elif task.sync_mode == "bisync":
            needs_resync = not task.bisync_initialized
            # Mark as bisync so progress_monitor skips it (no job_id)
            execution.rclone_job_id = -1  # sentinel: bisync running
            await db.commit()
            # Run bisync in background task
            asyncio.create_task(_run_bisync(
                task.id, execution.id, src, dst, extra_flags,
                needs_resync,
            ))
            return execution

        execution.rclone_job_id = job_id
        await db.commit()

        return execution

    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)
        execution.finished_at = datetime.utcnow()
        if execution.started_at:
            execution.duration_seconds = (execution.finished_at - execution.started_at).total_seconds()
        await db.commit()

        await ws_manager.broadcast({
            "type": "task_failed",
            "task_id": task.id,
            "execution_id": execution.id,
            "error": str(e),
        })
        raise


async def _run_bisync(task_id: int, execution_id: int, src: str, dst: str,
                      extra_flags: dict | None, needs_resync: bool):
    """Run bisync synchronously in a background coroutine."""
    from app.core.database import async_session
    from app.models.models import SyncTask, TaskExecution

    try:
        await rclone_client.start_bisync(src, dst, extra_flags=extra_flags, resync=needs_resync)
        # Success
        async with async_session() as db:
            execution = await db.get(TaskExecution, execution_id)
            if execution:
                execution.status = "completed"
                execution.finished_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration_seconds = (execution.finished_at - execution.started_at).total_seconds()
                execution.rclone_job_id = None
            if needs_resync:
                task = await db.get(SyncTask, task_id)
                if task:
                    task.bisync_initialized = True
            await db.commit()

        await ws_manager.broadcast({
            "type": "task_completed",
            "task_id": task_id,
            "execution_id": execution_id,
        })
    except Exception as e:
        logger.error(f"Bisync failed for task {task_id}: {e}")
        async with async_session() as db:
            execution = await db.get(TaskExecution, execution_id)
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.finished_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration_seconds = (execution.finished_at - execution.started_at).total_seconds()
                execution.rclone_job_id = None
            await db.commit()

        await ws_manager.broadcast({
            "type": "task_failed",
            "task_id": task_id,
            "execution_id": execution_id,
            "error": str(e),
        })
