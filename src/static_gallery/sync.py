from __future__ import annotations

from pathlib import Path


def sync_target(target: Path, expected_paths: set[Path]) -> None:
    if not target.exists():
        return

    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
        elif not path.is_dir() and path not in expected_paths:
            path.unlink()
