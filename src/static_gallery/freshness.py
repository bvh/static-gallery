from __future__ import annotations

from pathlib import Path


def compute_global_mtime(theme_dir: Path, config_path: Path | None) -> float:
    mtime = 0.0
    if theme_dir.is_dir():
        for entry in theme_dir.rglob("*"):
            if entry.is_file():
                mtime = max(mtime, entry.stat().st_mtime)
    if config_path is not None and config_path.is_file():
        mtime = max(mtime, config_path.stat().st_mtime)
    return mtime


def is_up_to_date(
    target_path: Path,
    source_path: Path,
    global_mtime: float,
    is_html: bool,
    *,
    extra_mtime: float = 0.0,
) -> bool:
    if not target_path.exists():
        return False
    target_mtime = target_path.stat().st_mtime
    if is_html:
        return target_mtime >= max(
            source_path.stat().st_mtime, global_mtime, extra_mtime
        )
    return target_mtime >= source_path.stat().st_mtime
