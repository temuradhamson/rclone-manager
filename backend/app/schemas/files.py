from pydantic import BaseModel


class FileItem(BaseModel):
    name: str
    path: str
    size: int = 0
    is_dir: bool = False
    mod_time: str | float | None = None
    total_bytes: int | None = None
    free_bytes: int | None = None


class RemoteInfo(BaseModel):
    name: str
    type: str
    total: int | None = None
    used: int | None = None
    free: int | None = None
