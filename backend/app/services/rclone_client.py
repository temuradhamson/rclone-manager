import httpx
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RcloneClient:
    def __init__(self):
        self.base_url = settings.rclone_rc_url

    async def _post(self, endpoint: str, data: dict | None = None, timeout: float = 30) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/{endpoint}", json=data or {}, timeout=timeout)
            r.raise_for_status()
            return r.json()

    async def list_remotes(self) -> list[str]:
        result = await self._post("config/listremotes")
        return result.get("remotes", [])

    async def remote_info(self, name: str) -> dict:
        result = await self._post("config/get", {"name": name})
        return result

    async def list_files(self, fs: str, remote: str = "", recurse: bool = False) -> list[dict]:
        result = await self._post("operations/list", {
            "fs": fs,
            "remote": remote,
            "opt": {
                "recurse": recurse,
                "noMimeType": True,
                "noModTime": False,
            }
        }, timeout=60)
        return result.get("list", [])

    async def about(self, fs: str) -> dict:
        try:
            result = await self._post("operations/about", {"fs": fs}, timeout=30)
            return result
        except Exception:
            return {}

    def _split_flags(self, extra_flags: dict | None) -> tuple[dict, dict]:
        """Split flags into RC params and _config overrides."""
        if not extra_flags:
            return {}, {}
        # These flags must go through _config for RC API
        config_keys = {"backupDir", "suffix", "immutable"}
        config = {}
        params = {}
        for k, v in extra_flags.items():
            if k in config_keys:
                # Convert camelCase to kebab-case for CLI flags
                cli_key = k
                if k == "backupDir":
                    cli_key = "BackupDir"
                elif k == "suffix":
                    cli_key = "Suffix"
                config[cli_key] = v
            else:
                params[k] = v
        return params, config

    async def start_copy(self, src_fs: str, dst_fs: str, src_remote: str = "", dst_remote: str = "",
                         extra_flags: dict | None = None, async_: bool = True) -> int | None:
        params, config = self._split_flags(extra_flags)
        data = {
            "srcFs": f"{src_fs}{src_remote}",
            "dstFs": f"{dst_fs}{dst_remote}",
            "_async": async_,
            **params,
        }
        if config:
            data["_config"] = config
        result = await self._post("sync/copy", data, timeout=10)
        return result.get("jobid")

    async def start_sync(self, src_fs: str, dst_fs: str, src_remote: str = "", dst_remote: str = "",
                         extra_flags: dict | None = None, async_: bool = True) -> int | None:
        params, config = self._split_flags(extra_flags)
        data = {
            "srcFs": f"{src_fs}{src_remote}",
            "dstFs": f"{dst_fs}{dst_remote}",
            "_async": async_,
            **params,
        }
        if config:
            data["_config"] = config
        result = await self._post("sync/sync", data, timeout=10)
        return result.get("jobid")

    async def start_bisync(self, path1: str, path2: str,
                           extra_flags: dict | None = None, async_: bool = True) -> int | None:
        params, config = self._split_flags(extra_flags)
        data = {
            "path1": path1,
            "path2": path2,
            "_async": async_,
            **params,
        }
        if config:
            data["_config"] = config
        result = await self._post("sync/bisync", data, timeout=10)
        return result.get("jobid")

    async def job_status(self, job_id: int) -> dict:
        result = await self._post("job/status", {"jobid": job_id})
        return result

    async def job_list(self) -> dict:
        result = await self._post("job/list")
        return result

    async def job_stop(self, job_id: int) -> None:
        await self._post("job/stop", {"jobid": job_id})

    async def get_stats(self, group: str | None = None) -> dict:
        data = {}
        if group:
            data["group"] = group
        result = await self._post("core/stats", data)
        return result

    async def get_transferred(self, group: str | None = None) -> list[dict]:
        data = {}
        if group:
            data["group"] = group
        result = await self._post("core/transferred", data)
        return result.get("transferred", [])


rclone_client = RcloneClient()
