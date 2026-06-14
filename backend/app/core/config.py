from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    rclone_path: str = "C:/rclone/rclone.exe"
    rclone_rc_port: int = 5573
    database_url: str = "sqlite+aiosqlite:///data/rclone_manager.db"
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def rclone_rc_url(self) -> str:
        return f"http://localhost:{self.rclone_rc_port}"

    @property
    def db_path(self) -> Path:
        url = self.database_url.replace("sqlite+aiosqlite:///", "")
        return Path(url)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
