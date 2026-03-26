import os
import string
from pathlib import Path

from app.services.rclone_client import rclone_client


async def list_remote_files(fs: str, remote: str = "") -> list[dict]:
    items = await rclone_client.list_files(fs, remote)
    result = []
    for item in items:
        result.append({
            "name": item.get("Name", ""),
            "path": item.get("Path", ""),
            "size": item.get("Size", 0),
            "is_dir": item.get("IsDir", False),
            "mod_time": item.get("ModTime", ""),
        })
    result.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return result


def list_local_drives() -> list[dict]:
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                usage = os.statvfs(drive) if hasattr(os, "statvfs") else None
                total = free = 0
                # Windows: use ctypes
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    drive, None, ctypes.byref(total_bytes), ctypes.byref(free_bytes)
                )
                total = total_bytes.value
                free = free_bytes.value
                drives.append({
                    "name": f"{letter}:",
                    "path": drive,
                    "is_dir": True,
                    "size": 0,
                    "total_bytes": total,
                    "free_bytes": free,
                })
            except Exception:
                drives.append({
                    "name": f"{letter}:",
                    "path": drive,
                    "is_dir": True,
                    "size": 0,
                })
    return drives


def list_local_path(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return []
    result = []
    try:
        for entry in os.scandir(path):
            try:
                stat = entry.stat()
                result.append({
                    "name": entry.name,
                    "path": entry.path.replace("\\", "/"),
                    "size": stat.st_size if entry.is_file() else 0,
                    "is_dir": entry.is_dir(),
                    "mod_time": stat.st_mtime,
                })
            except (PermissionError, OSError):
                continue
    except PermissionError:
        return []
    result.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return result
