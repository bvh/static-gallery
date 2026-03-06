from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class FileType(Enum):
    MARKDOWN = auto()
    IMAGE = auto()
    STATIC = auto()


@dataclass
class SourceFile:
    file_type: FileType
    source_path: Path
    rel_path: Path
    html_target: Path | None = None
    asset_target: Path | None = None


@dataclass
class SourceDir:
    rel_path: Path
    files: list[SourceFile] = field(default_factory=list)
    children: dict[str, SourceDir] = field(default_factory=dict)


def all_target_paths(root: SourceDir) -> set[Path]:
    paths: set[Path] = set()
    for f in root.files:
        if f.html_target is not None:
            paths.add(f.html_target)
        if f.asset_target is not None:
            paths.add(f.asset_target)
    for child in root.children.values():
        paths.update(all_target_paths(child))
    return paths
