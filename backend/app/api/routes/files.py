from fastapi import APIRouter, Query

from app.schemas.files import FileItem
from app.services.file_browser import list_remote_files, list_local_drives, list_local_path

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/list")
async def list_files(
    fs: str = Query(..., description="Filesystem, e.g. 'onedrive:'"),
    path: str = Query("", description="Path within the filesystem"),
) -> list[FileItem]:
    items = await list_remote_files(fs, path)
    return [FileItem(**item) for item in items]


@router.get("/local/drives")
async def get_local_drives() -> list[FileItem]:
    drives = list_local_drives()
    return [FileItem(**d) for d in drives]


@router.get("/local")
async def list_local(
    path: str = Query(..., description="Local path, e.g. 'C:/'"),
) -> list[FileItem]:
    items = list_local_path(path)
    return [FileItem(**item) for item in items]
