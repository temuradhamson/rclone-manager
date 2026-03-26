import asyncio
import subprocess
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class RcloneDaemon:
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self.rclone_path = settings.rclone_path
        self.port = settings.rclone_rc_port
        self.base_url = settings.rclone_rc_url

    async def start(self):
        logger.info(f"Starting rclone daemon on port {self.port}...")
        self.process = subprocess.Popen(
            [
                self.rclone_path, "rcd",
                "--rc-addr", f"localhost:{self.port}",
                "--rc-no-auth",
                "--log-level", "INFO",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for _ in range(30):
            if await self.health_check():
                logger.info("rclone daemon is ready")
                return
            await asyncio.sleep(0.5)
        raise RuntimeError("rclone daemon failed to start within 15 seconds")

    async def stop(self):
        if not self.process:
            return
        logger.info("Stopping rclone daemon...")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.base_url}/core/quit", timeout=5)
        except Exception:
            pass
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()
        self.process = None
        logger.info("rclone daemon stopped")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{self.base_url}/rc/noop", timeout=2)
                return r.status_code == 200
        except Exception:
            return False

    async def restart(self):
        await self.stop()
        await self.start()


daemon = RcloneDaemon()
