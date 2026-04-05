"""VueFinder-compatible file manager API for rclone remotes and local drives."""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from app.services.rclone_client import rclone_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fm", tags=["filemanager"])

LOCAL_STORAGES = {
    "onedrive:": "onedrive:",
    "C:": "C:/",
    "D:": "D:/",
    "E:": "E:/",
    "F:": "F:/",
    "G:": "G:/",
}


def _is_remote(path: str) -> bool:
    """Check if path is rclone remote (e.g. onedrive:folder)."""
    return ":" in path and not (len(path) >= 2 and path[1] == ":" and path[0].isalpha())


def _to_dir_entry(name: str, path: str, is_dir: bool, size: int = 0, mtime: str = ""):
    return {
        "path": path,
        "basename": name,
        "extension": "" if is_dir else Path(name).suffix.lstrip("."),
        "type": "dir" if is_dir else "file",
        "size": size,
        "last_modified": mtime or datetime.now().isoformat(),
    }


def _list_local(directory: str) -> list[dict]:
    items = []
    try:
        for entry in os.scandir(directory):
            try:
                stat = entry.stat()
                items.append(_to_dir_entry(
                    name=entry.name,
                    path=os.path.join(directory, entry.name).replace("\\", "/"),
                    is_dir=entry.is_dir(),
                    size=stat.st_size if not entry.is_dir() else 0,
                    mtime=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                ))
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError) as e:
        logger.warning(f"Cannot list {directory}: {e}")
    return sorted(items, key=lambda x: (x["type"] != "dir", x["basename"].lower()))


async def _list_remote(fs: str, remote: str = "") -> list[dict]:
    try:
        files = await rclone_client.list_files(fs, remote)
        items = []
        for f in files:
            full_path = f"{fs}{remote}/{f['Name']}" if remote else f"{fs}{f['Name']}"
            items.append(_to_dir_entry(
                name=f["Name"],
                path=full_path,
                is_dir=f.get("IsDir", False),
                size=f.get("Size", 0),
                mtime=f.get("ModTime", ""),
            ))
        return sorted(items, key=lambda x: (x["type"] != "dir", x["basename"].lower()))
    except Exception as e:
        logger.error(f"Remote list error: {e}")
        return []


def _build_response(dirname: str, files: list[dict]) -> dict:
    remotes_list = list(LOCAL_STORAGES.keys())
    return {
        "files": files,
        "dirname": dirname,
        "storages": remotes_list,
        "read_only": False,
    }


@router.api_route("/list", methods=["GET", "POST"])
async def fm_list(request: Request, path: str = ""):
    if request.method == "POST":
        try:
            data = await request.json()
            path = data.get("path", path).strip()
        except Exception:
            pass
    path = path.strip()

    if not path:
        # Root: show storages
        items = [_to_dir_entry(name=k, path=k + "/", is_dir=True) for k in LOCAL_STORAGES]
        return _build_response("/", items)

    path = path.replace("\\", "/").rstrip("/")

    if _is_remote(path):
        parts = path.split(":", 1)
        fs = parts[0] + ":"
        remote = parts[1].lstrip("/") if len(parts) > 1 else ""
        files = await _list_remote(fs, remote)
        return _build_response(path, files)
    else:
        # Normalize drive paths like "C:" -> "C:/"
        if len(path) == 2 and path[1] == ":":
            path = path + "/"
        files = _list_local(path)
        return _build_response(path, files)


@router.post("/createFolder")
async def fm_create_folder(request: Request):
    data = await request.json()
    path = data.get("path", "").replace("\\", "/").rstrip("/")
    name = data.get("name", "")

    full_path = f"{path}/{name}"

    if _is_remote(full_path):
        fs, remote = full_path.split(":", 1)
        await rclone_client._post("operations/mkdir", {"fs": fs + ":", "remote": remote.lstrip("/")})
    else:
        os.makedirs(full_path, exist_ok=True)

    files = await _list_remote(path.split(":")[0] + ":", path.split(":", 1)[1].lstrip("/")) if _is_remote(path) else _list_local(path)
    return _build_response(path, files)


@router.post("/delete")
async def fm_delete(request: Request):
    data = await request.json()
    items = data.get("items", [])
    path = data.get("path", "").replace("\\", "/").rstrip("/")

    for item in items:
        item_path = item.get("path", "").replace("\\", "/")
        is_dir = item.get("type") == "dir"

        if _is_remote(item_path):
            fs, remote = item_path.split(":", 1)
            fs = fs + ":"
            remote = remote.lstrip("/")
            if is_dir:
                await rclone_client._post("operations/purge", {"fs": fs, "remote": remote}, timeout=120)
            else:
                await rclone_client._post("operations/deletefile", {"fs": fs, "remote": remote})
        else:
            if is_dir:
                shutil.rmtree(item_path, ignore_errors=True)
            else:
                try:
                    os.remove(item_path)
                except OSError:
                    pass

    files = await _list_remote(path.split(":")[0] + ":", path.split(":", 1)[1].lstrip("/")) if _is_remote(path) else _list_local(path)
    return _build_response(path, files)


@router.post("/rename")
async def fm_rename(request: Request):
    data = await request.json()
    path = data.get("path", "").replace("\\", "/").rstrip("/")
    item = data.get("item", "").replace("\\", "/")
    new_name = data.get("name", "")

    old_path = item
    parent = "/".join(old_path.rstrip("/").split("/")[:-1])
    new_path = f"{parent}/{new_name}"

    if _is_remote(old_path):
        fs_old, remote_old = old_path.split(":", 1)
        fs_new, remote_new = new_path.split(":", 1)
        await rclone_client._post("operations/movefile", {
            "srcFs": fs_old + ":",
            "srcRemote": remote_old.lstrip("/"),
            "dstFs": fs_new + ":",
            "dstRemote": remote_new.lstrip("/"),
        })
    else:
        os.rename(old_path, new_path)

    files = await _list_remote(path.split(":")[0] + ":", path.split(":", 1)[1].lstrip("/")) if _is_remote(path) else _list_local(path)
    return _build_response(path, files)


@router.post("/move")
async def fm_move(request: Request):
    data = await request.json()
    sources = data.get("sources", [])
    destination = data.get("destination", "").replace("\\", "/").rstrip("/")

    for src in sources:
        src = src.replace("\\", "/")
        name = src.rstrip("/").split("/")[-1]
        dst = f"{destination}/{name}"

        if _is_remote(src) or _is_remote(dst):
            fs_s, r_s = src.split(":", 1) if ":" in src else ("", src)
            fs_d, r_d = dst.split(":", 1) if ":" in dst else ("", dst)
            await rclone_client._post("operations/movefile", {
                "srcFs": (fs_s + ":") if fs_s else "",
                "srcRemote": r_s.lstrip("/"),
                "dstFs": (fs_d + ":") if fs_d else "",
                "dstRemote": r_d.lstrip("/"),
            })
        else:
            shutil.move(src, dst)

    files = await _list_remote(destination.split(":")[0] + ":", destination.split(":", 1)[1].lstrip("/")) if _is_remote(destination) else _list_local(destination)
    return _build_response(destination, files)


@router.post("/copy")
async def fm_copy(request: Request):
    data = await request.json()
    sources = data.get("sources", [])
    destination = data.get("destination", "").replace("\\", "/").rstrip("/")

    for src in sources:
        src = src.replace("\\", "/")
        name = src.rstrip("/").split("/")[-1]
        dst = f"{destination}/{name}"

        if _is_remote(src) or _is_remote(dst):
            fs_s, r_s = src.split(":", 1) if ":" in src else ("", src)
            fs_d, r_d = dst.split(":", 1) if ":" in dst else ("", dst)
            await rclone_client._post("operations/copyfile", {
                "srcFs": (fs_s + ":") if fs_s else "",
                "srcRemote": r_s.lstrip("/"),
                "dstFs": (fs_d + ":") if fs_d else "",
                "dstRemote": r_d.lstrip("/"),
            })
        else:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    files = await _list_remote(destination.split(":")[0] + ":", destination.split(":", 1)[1].lstrip("/")) if _is_remote(destination) else _list_local(destination)
    return _build_response(destination, files)


@router.post("/upload")
async def fm_upload(path: str = Form(""), files: list[UploadFile] = File(...)):
    path = path.replace("\\", "/").rstrip("/")

    for f in files:
        if _is_remote(path):
            content = await f.read()
            fs, remote = path.split(":", 1)
            # For remote upload, write to temp then rclone copy
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f.filename) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                await rclone_client._post("operations/copyfile", {
                    "srcFs": "/",
                    "srcRemote": tmp_path.replace("\\", "/"),
                    "dstFs": fs + ":",
                    "dstRemote": f"{remote.lstrip('/')}/{f.filename}",
                })
            finally:
                os.unlink(tmp_path)
        else:
            dest = os.path.join(path, f.filename)
            content = await f.read()
            with open(dest, "wb") as out:
                out.write(content)

    result_files = await _list_remote(path.split(":")[0] + ":", path.split(":", 1)[1].lstrip("/")) if _is_remote(path) else _list_local(path)
    return _build_response(path, result_files)


MIME_MAP = {
    # Video
    "mp4": "video/mp4", "mkv": "video/x-matroska", "avi": "video/x-msvideo",
    "webm": "video/webm", "mov": "video/quicktime", "wmv": "video/x-ms-wmv",
    "flv": "video/x-flv", "m4v": "video/x-m4v", "ts": "video/mp2t",
    # Audio
    "mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
    "ogg": "audio/ogg", "m4a": "audio/mp4", "aac": "audio/aac", "wma": "audio/x-ms-wma",
    # Images
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml", "bmp": "image/bmp",
    # Documents
    "pdf": "application/pdf", "txt": "text/plain", "html": "text/html",
    "css": "text/css", "js": "text/javascript", "json": "application/json",
    "xml": "text/xml", "csv": "text/csv", "md": "text/markdown",
}


def _get_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return MIME_MAP.get(ext, "application/octet-stream")


@router.get("/preview")
async def fm_preview(path: str):
    """Stream file for in-browser preview (video, audio, images, docs)."""
    path = path.replace("\\", "/")
    if _is_remote(path) or not os.path.isfile(path):
        return JSONResponse({"error": "Preview only for local files"}, 400)

    mime = _get_mime(path)
    return FileResponse(path, media_type=mime, filename=os.path.basename(path))


@router.get("/download")
async def fm_download(path: str):
    path = path.replace("\\", "/")
    if not _is_remote(path) and os.path.isfile(path):
        return FileResponse(path, filename=os.path.basename(path), media_type="application/octet-stream")
    return JSONResponse({"error": "Download not supported for remote files"}, 400)


@router.post("/search")
async def fm_search(request: Request):
    data = await request.json()
    path = data.get("path", "").replace("\\", "/").rstrip("/")
    query = data.get("filter", "").lower()

    if not path or not query:
        return []

    results = []
    if not _is_remote(path):
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                if query in name.lower():
                    full = os.path.join(root, name).replace("\\", "/")
                    is_dir = os.path.isdir(full)
                    results.append(_to_dir_entry(name, full, is_dir))
                    if len(results) >= 50:
                        return results
    return results
