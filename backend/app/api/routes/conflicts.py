"""Bisync conflict management API."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.conflict_scanner import scan_conflicts, resolve_conflict

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])


@router.get("")
async def list_conflicts(directory: str = Query(...)):
    """Scan directory for .conflict files."""
    conflicts = scan_conflicts(directory)
    return {"conflicts": conflicts, "total": len(conflicts)}


class ResolveRequest(BaseModel):
    path: str
    action: str = "delete_conflict"  # delete_conflict | keep_conflict


@router.post("/resolve")
async def resolve(data: ResolveRequest):
    """Resolve a conflict file."""
    ok = resolve_conflict(data.path, data.action)
    return {"ok": ok}
