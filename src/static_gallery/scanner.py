from __future__ import annotations

from pathlib import Path

from static_gallery.model import FileType, SourceDir, SourceFile


_IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".webp", ".png"}


def _classify(path: Path) -> FileType:
    ext = path.suffix.lower()
    if ext == ".md":
        return FileType.MARKDOWN
    if ext in _IMAGE_EXTENSIONS:
        return FileType.IMAGE
    return FileType.STATIC


def _has_dot_component(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def _ensure_dir(root: SourceDir, rel: Path) -> SourceDir:
    node = root
    for part in rel.parts:
        if part not in node.children:
            child_rel = node.rel_path / part
            node.children[part] = SourceDir(rel_path=child_rel)
        node = node.children[part]
    return node


def _resolve_and_assign_targets(node: SourceDir, target: Path) -> None:
    md_stems = {f.rel_path.stem.lower() for f in node.files if f.file_type == FileType.MARKDOWN}

    for f in node.files:
        if f.file_type == FileType.IMAGE and f.rel_path.stem.lower() in md_stems:
            f.file_type = FileType.STATIC

        rel = f.rel_path
        if f.file_type == FileType.MARKDOWN:
            f.html_target = target / rel.with_suffix(".html")
        elif f.file_type == FileType.IMAGE:
            f.html_target = target / rel.with_suffix(".html")
            f.asset_target = target / rel
        else:
            f.asset_target = target / rel

    for child in node.children.values():
        _resolve_and_assign_targets(child, target)


def scan(source: Path, target: Path, config_filename: str) -> SourceDir:
    config_path = source / config_filename
    root = SourceDir(rel_path=Path("."))

    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(source)
        if _has_dot_component(rel):
            continue
        if path == config_path:
            continue

        file_type = _classify(path)
        parent_rel = rel.parent
        if parent_rel == Path("."):
            dir_node = root
        else:
            dir_node = _ensure_dir(root, parent_rel)

        dir_node.files.append(SourceFile(
            file_type=file_type,
            source_path=path,
            rel_path=rel,
        ))

    _resolve_and_assign_targets(root, target)
    return root
