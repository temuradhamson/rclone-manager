"""Scan for bisync conflict files."""

import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def scan_conflicts(directory: str) -> list[dict]:
    """Find .conflict files created by rclone bisync."""
    conflicts = []
    try:
        for root, dirs, files in os.walk(directory):
            for f in files:
                if ".conflict" in f.lower():
                    full_path = os.path.join(root, f)
                    try:
                        stat = os.stat(full_path)
                        conflicts.append({
                            "path": full_path,
                            "name": f,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "dir": root,
                        })
                    except OSError:
                        pass
    except Exception as e:
        logger.error(f"Conflict scan error in {directory}: {e}")
    return sorted(conflicts, key=lambda x: x["modified"], reverse=True)


def resolve_conflict(conflict_path: str, action: str = "keep_conflict") -> bool:
    """Resolve a conflict file.

    Actions:
    - keep_conflict: replace original with conflict version
    - delete_conflict: remove conflict file
    """
    try:
        if action == "delete_conflict":
            os.remove(conflict_path)
            return True
        elif action == "keep_conflict":
            # Remove .conflict1, .conflict2 etc suffix to get original name
            original = conflict_path
            for suffix in [".conflict1", ".conflict2", ".conflict"]:
                if suffix in original:
                    original = original.replace(suffix, "")
                    break
            if original != conflict_path and os.path.exists(original):
                os.replace(conflict_path, original)
                return True
            elif original != conflict_path:
                os.rename(conflict_path, original)
                return True
        return False
    except Exception as e:
        logger.error(f"Resolve conflict failed: {e}")
        return False
