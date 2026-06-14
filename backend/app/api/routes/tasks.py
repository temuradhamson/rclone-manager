from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import SyncTask, FileRule, Schedule
from app.schemas.tasks import (
    TaskCreate, TaskUpdate, TaskResponse,
    RuleCreate, RuleResponse,
    ScheduleCreate, ScheduleResponse,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyncTask).order_by(SyncTask.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = SyncTask(**data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    await db.delete(task)
    await db.commit()


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.is_enabled = not task.is_enabled
    await db.commit()
    await db.refresh(task)
    return task


# --- Rules ---

@router.get("/{task_id}/rules", response_model=list[RuleResponse])
async def list_rules(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FileRule).where(FileRule.task_id == task_id).order_by(FileRule.priority.desc())
    )
    return result.scalars().all()


@router.post("/{task_id}/rules", response_model=RuleResponse, status_code=201)
async def create_rule(task_id: int, data: RuleCreate, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    rule = FileRule(task_id=task_id, **data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await db.get(FileRule, rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    await db.delete(rule)
    await db.commit()


# --- Schedule ---

@router.get("/{task_id}/schedule", response_model=ScheduleResponse | None)
async def get_schedule(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Schedule).where(Schedule.task_id == task_id)
    )
    return result.scalar_one_or_none()


@router.put("/{task_id}/schedule", response_model=ScheduleResponse)
async def set_schedule(task_id: int, data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    task = await db.get(SyncTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    result = await db.execute(select(Schedule).where(Schedule.task_id == task_id))
    schedule = result.scalar_one_or_none()
    if schedule:
        for key, value in data.model_dump().items():
            setattr(schedule, key, value)
    else:
        schedule = Schedule(task_id=task_id, **data.model_dump())
        db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{task_id}/schedule", status_code=204)
async def delete_schedule(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.task_id == task_id))
    schedule = result.scalar_one_or_none()
    if schedule:
        await db.delete(schedule)
        await db.commit()
