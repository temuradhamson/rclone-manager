from fastapi import APIRouter

from app.services.rclone_client import rclone_client
from app.schemas.files import RemoteInfo

router = APIRouter(prefix="/api/remotes", tags=["remotes"])


@router.get("")
async def list_remotes() -> list[RemoteInfo]:
    names = await rclone_client.list_remotes()
    remotes = []
    for name in names:
        info = await rclone_client.remote_info(name)
        about = await rclone_client.about(f"{name}:")
        remotes.append(RemoteInfo(
            name=name,
            type=info.get("type", "unknown"),
            total=about.get("total"),
            used=about.get("used"),
            free=about.get("free"),
        ))
    return remotes


@router.get("/{name}/info")
async def get_remote_info(name: str) -> dict:
    info = await rclone_client.remote_info(name)
    about = await rclone_client.about(f"{name}:")
    return {"config": info, "about": about}
