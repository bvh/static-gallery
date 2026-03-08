from __future__ import annotations

from pathlib import Path

from static_gallery.model import Node, NodeType


def node_segments(node: Node) -> list[str]:
    parts = []
    current = node
    while current is not None:
        if current.name:
            parts.append(current.name)
        current = current.parent
    parts.reverse()
    return parts


def target_paths(
    node: Node, target: Path, *, has_listing: bool = False
) -> tuple[Path | None, Path | None]:
    segs = node_segments(node)
    prefix = Path(*segs) if segs else Path(".")

    if node.source is None:
        if has_listing and node.children:
            return target / prefix / "index.html", None
        return None, None

    if node.node_type == NodeType.MARKDOWN:
        if node.is_index:
            html = target / prefix / "index.html"
        else:
            html = target / prefix.parent / (node.name + ".html")
        return html, None

    elif node.node_type == NodeType.IMAGE:
        html = target / prefix.parent / (node.name + ".html")
        asset = target / prefix.parent / node.source.name
        return html, asset

    else:  # STATIC
        asset = target / prefix.parent / node.source.name
        return None, asset
