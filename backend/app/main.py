import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.rclone_daemon import daemon
from app.models.models import Base
from app.services.progress_monitor import start_monitor, stop_monitor

from app.api.routes import files, remotes, tasks, execution, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directory exists
    db_dir = settings.db_path.parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready")

    # Start rclone daemon
    await daemon.start()

    # Start progress monitor
    start_monitor()

    yield

    # Shutdown
    stop_monitor()
    await daemon.stop()
    await engine.dispose()


app = FastAPI(title="Rclone Manager", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(remotes.router)
app.include_router(tasks.router)
app.include_router(execution.router)
app.include_router(ws.router)


@app.get("/api/health")
async def health():
    rclone_ok = await daemon.health_check()
    return {"status": "ok", "rclone": rclone_ok}
