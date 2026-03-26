from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    src_type: str  # remote, local
    src_path: str
    dst_type: str
    dst_path: str
    sync_mode: str  # copy_to_local, copy_to_remote, sync_to_local, sync_to_remote, bisync
    extra_flags: str | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    src_type: str | None = None
    src_path: str | None = None
    dst_type: str | None = None
    dst_path: str | None = None
    sync_mode: str | None = None
    is_enabled: bool | None = None
    extra_flags: str | None = None


class TaskResponse(BaseModel):
    id: int
    name: str
    description: str | None
    src_type: str
    src_path: str
    dst_type: str
    dst_path: str
    sync_mode: str
    is_enabled: bool
    extra_flags: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleCreate(BaseModel):
    rule_type: str  # on_delete, on_modify, on_conflict
    action: str  # backup, delete_immediate, move_to_trash, skip
    backup_dir: str | None = None
    retention_days: int | None = None
    trash_dir: str | None = None
    file_pattern: str | None = None
    priority: int = 0


class RuleResponse(BaseModel):
    id: int
    task_id: int
    rule_type: str
    action: str
    backup_dir: str | None
    retention_days: int | None
    trash_dir: str | None
    file_pattern: str | None
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    schedule_type: str  # interval, cron
    interval_seconds: int | None = None
    cron_expression: str | None = None
    is_active: bool = True


class ScheduleResponse(BaseModel):
    id: int
    task_id: int
    schedule_type: str
    interval_seconds: int | None
    cron_expression: str | None
    is_active: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: int
    task_id: int | None
    rclone_job_id: int | None
    status: str
    trigger: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    bytes_transferred: int | None
    files_transferred: int | None
    files_checked: int | None
    files_deleted: int | None
    errors_count: int | None
    error_message: str | None

    model_config = {"from_attributes": True}
