from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import SyncTask, TaskExecution
from app.services.sync_engine import run_task
from app.services.rclone_client import rclone_client
from app.schemas.tasks import ExecutionResponse

router = APIRouter(prefix="/api/tasks", tags=["execution"])


@router.post("/{task_id}/run", response_model=ExecutionResponse)
async def run(task_id: int, dry_run: bool = Query(False), db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    execution = await run_task(task, db, trigger="manual")
    return execution


@router.post("/{task_id}/stop")
async def stop(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskExecution).where(
            TaskExecution.task_id == task_id,
            TaskExecution.status == "running",
        )
    )
    execution = result.scalar_one_or_none()
    if not execution or not execution.rclone_job_id:
        raise HTTPException(404, "No running execution found")
    await rclone_client.job_stop(execution.rclone_job_id)
    return {"status": "stopping"}


@router.get("/{task_id}/status")
async def status(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskExecution).where(TaskExecution.task_id == task_id)
        .order_by(TaskExecution.started_at.desc()).limit(1)
    )
    execution = result.scalar_one_or_none()
    if not execution:
        return {"status": "never_run"}
    resp = {"status": execution.status, "execution_id": execution.id}
    if execution.rclone_job_id and execution.status == "running":
        try:
            stats = await rclone_client.get_stats()
            resp["progress"] = stats
        except Exception:
            pass
    return resp


@router.get("/executions/list", response_model=list[ExecutionResponse])
async def list_executions(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskExecution)
        .order_by(TaskExecution.started_at.desc())
        .offset(offset).limit(limit)
    )
    return result.scalars().all()
