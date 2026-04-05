from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, BigInteger, Float, Text, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Remote(Base):
    __tablename__ = "remotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    type: Mapped[str] = mapped_column(String(50))
    config_json: Mapped[str | None] = mapped_column(Text)
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SyncTask(Base):
    __tablename__ = "sync_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    src_type: Mapped[str] = mapped_column(String(10))  # "remote" or "local"
    src_path: Mapped[str] = mapped_column(String(1024))
    dst_type: Mapped[str] = mapped_column(String(10))
    dst_path: Mapped[str] = mapped_column(String(1024))
    sync_mode: Mapped[str] = mapped_column(String(20))  # copy_to_local, copy_to_remote, sync_to_local, sync_to_remote, bisync
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    bisync_initialized: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_flags: Mapped[str | None] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    rules: Mapped[list["FileRule"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    schedule: Mapped["Schedule | None"] = relationship(back_populates="task", cascade="all, delete-orphan", uselist=False)
    executions: Mapped[list["TaskExecution"]] = relationship(back_populates="task")


class FileRule(Base):
    __tablename__ = "file_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("sync_tasks.id", ondelete="CASCADE"))
    rule_type: Mapped[str] = mapped_column(String(20))  # on_delete, on_modify, on_conflict
    action: Mapped[str] = mapped_column(String(20))  # backup, delete_immediate, move_to_trash, skip
    backup_dir: Mapped[str | None] = mapped_column(String(1024))
    retention_days: Mapped[int | None] = mapped_column(Integer)
    trash_dir: Mapped[str | None] = mapped_column(String(1024))
    file_pattern: Mapped[str | None] = mapped_column(String(255))  # glob pattern
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["SyncTask"] = relationship(back_populates="rules")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("sync_tasks.id", ondelete="CASCADE"), unique=True)
    schedule_type: Mapped[str] = mapped_column(String(10))  # interval, cron
    interval_seconds: Mapped[int | None] = mapped_column(Integer)
    cron_expression: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["SyncTask"] = relationship(back_populates="schedule")


class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("sync_tasks.id", ondelete="SET NULL"))
    rclone_job_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))  # running, completed, failed, cancelled
    trigger: Mapped[str | None] = mapped_column(String(20))  # manual, scheduled, startup
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    bytes_transferred: Mapped[int | None] = mapped_column(BigInteger)
    files_transferred: Mapped[int | None] = mapped_column(Integer)
    files_checked: Mapped[int | None] = mapped_column(Integer)
    files_deleted: Mapped[int | None] = mapped_column(Integer)
    errors_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    stats_json: Mapped[str | None] = mapped_column(Text)
    log_output: Mapped[str | None] = mapped_column(Text)

    task: Mapped["SyncTask | None"] = relationship(back_populates="executions")
    transfers: Mapped[list["TransferLog"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


class TransferLog(Base):
    __tablename__ = "transfer_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("task_executions.id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(1024))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str | None] = mapped_column(String(20))  # copy, delete, move, skip
    status: Mapped[str | None] = mapped_column(String(10))  # ok, error
    error: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    execution: Mapped["TaskExecution"] = relationship(back_populates="transfers")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    remote_name: Mapped[str] = mapped_column(String(255), index=True)
    bytes_uploaded: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_downloaded: Mapped[int] = mapped_column(BigInteger, default=0)
    files_transferred: Mapped[int] = mapped_column(Integer, default=0)
    sync_count: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_bot_token: Mapped[str | None] = mapped_column(String(255))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50))
    notify_on_error: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_on_conflict: Mapped[bool] = mapped_column(Boolean, default=True)
