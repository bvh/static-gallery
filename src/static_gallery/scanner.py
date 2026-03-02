from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class TaskType(Enum):
    MARKDOWN = auto()
    IMAGE = auto()
    STATIC = auto()


_IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".webp", ".png"}


@dataclass(frozen=True)
class BuildTask:
    task_type: TaskType
    source_path: Path
    target_paths: list[Path] = field(hash=False)


def _classify(path: Path) -> TaskType:
    ext = path.suffix.lower()
    if ext == ".md":
        return TaskType.MARKDOWN
    if ext in _IMAGE_EXTENSIONS:
        return TaskType.IMAGE
    return TaskType.STATIC


def _has_dot_component(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def scan(source: Path, target: Path, config_filename: str) -> list[BuildTask]:
    config_path = source / config_filename

    # Collect and classify all files
    by_dir: dict[Path, list[tuple[Path, TaskType]]] = defaultdict(list)

    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(source)
        if _has_dot_component(rel):
            continue
        if path == config_path:
            continue

        task_type = _classify(path)
        by_dir[path.parent].append((path, task_type))

    # Resolve collisions per directory
    tasks: list[BuildTask] = []

    for dir_path, entries in by_dir.items():
        md_stems = {p.stem.lower() for p, t in entries if t == TaskType.MARKDOWN}

        for path, task_type in entries:
            if task_type == TaskType.IMAGE and path.stem.lower() in md_stems:
                task_type = TaskType.STATIC

            rel = path.relative_to(source)
            if task_type == TaskType.MARKDOWN:
                target_paths = [target / rel.with_suffix(".html")]
            elif task_type == TaskType.IMAGE:
                target_paths = [target / rel.with_suffix(".html"), target / rel]
            else:
                target_paths = [target / rel]

            tasks.append(BuildTask(task_type, path, target_paths))

    return tasks
