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

        # Parse extra_flags from task config
        if task.extra_flags:
            try:
                task_flags = json.loads(task.extra_flags)
                if isinstance(task_flags, dict):
                    extra_flags.update(task_flags)
            except json.JSONDecodeError:
                pass

        # Determine source and destination
        src = task.src_path if task.src_type == "remote" else task.src_path.rstrip("/") + "/"
        dst = task.dst_path if task.dst_type == "remote" else task.dst_path.rstrip("/") + "/"

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
            job_id = await rclone_client.start_bisync(src, dst, extra_flags=extra_flags)

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
