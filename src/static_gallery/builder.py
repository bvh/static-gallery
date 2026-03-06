from __future__ import annotations

import shutil
from pathlib import Path

import jinja2
from markupsafe import Markup
import mistletoe

from static_gallery.config import parse_front_matter
from static_gallery.errors import error
from static_gallery.model import Node, NodeType


def _node_segments(node: Node) -> list[str]:
    parts = []
    current = node
    while current is not None:
        if current.name:
            parts.append(current.name)
        current = current.parent
    parts.reverse()
    return parts


def _target_paths(node: Node, target: Path) -> tuple[Path | None, Path | None]:
    if node.source is None:
        return None, None

    segs = _node_segments(node)
    prefix = Path(*segs) if segs else Path(".")
    is_index = node.source.name.lower() == "index.md"

    if node.node_type == NodeType.MARKDOWN:
        if is_index:
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


def build(
    tree: Node,
    site_config: dict[str, str],
    source: Path,
    target: Path,
) -> None:
    theme_dir = source / ".theme"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(theme_dir)),
            autoescape=True,
        )
    except Exception as exc:
        error(f"Cannot load templates from {theme_dir}: {exc}")

    expected: set[Path] = set()
    _build_node(tree, site_config, env, target, expected)
    _sync_target(target, expected)


def _build_node(
    node: Node,
    site_config: dict[str, str],
    env: jinja2.Environment,
    target: Path,
    expected: set[Path],
) -> None:
    html_target, asset_target = _target_paths(node, target)

    if html_target is not None:
        expected.add(html_target)
    if asset_target is not None:
        expected.add(asset_target)

    if node.node_type == NodeType.MARKDOWN and node.source is not None:
        _build_markdown(node, html_target, site_config, env)
    elif node.node_type == NodeType.IMAGE:
        _build_image(node, html_target, asset_target, site_config, env)
    elif node.node_type == NodeType.STATIC:
        _build_static(node, asset_target)

    for child in node.children:
        _build_node(child, site_config, env, target, expected)


def _load_template(env: jinja2.Environment, name: str) -> jinja2.Template:
    try:
        return env.get_template(f"{name}.html")
    except jinja2.TemplateNotFound:
        error(f"Missing template: .theme/{name}.html")
    except jinja2.TemplateSyntaxError as exc:
        error(f"Template syntax error in .theme/{name}.html: {exc}")


def _build_markdown(
    node: Node,
    html_target: Path,
    site_config: dict[str, str],
    env: jinja2.Environment,
) -> None:
    try:
        text = node.source.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"Cannot read {node.source}: {exc}")

    metadata, body = parse_front_matter(text)
    html_content = mistletoe.markdown(body)

    template_type = metadata.get("type", "page")
    if "type" in metadata:
        del metadata["type"]
    template = _load_template(env, template_type)

    output = template.render(site=site_config, page=metadata, content=Markup(html_content))

    html_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        html_target.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {html_target}: {exc}")


def _build_image(
    node: Node,
    html_target: Path,
    asset_target: Path,
    site_config: dict[str, str],
    env: jinja2.Environment,
) -> None:
    stem = node.source.stem
    title = stem.replace("-", " ").replace("_", " ").title()
    filename = node.source.name

    metadata = {"title": title, "src": filename}
    template = _load_template(env, "image")

    output = template.render(site=site_config, page=metadata, content=filename)

    html_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        html_target.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {html_target}: {exc}")

    try:
        shutil.copy2(node.source, asset_target)
    except OSError as exc:
        error(f"Cannot copy {node.source} to {asset_target}: {exc}")


def _build_static(node: Node, asset_target: Path) -> None:
    asset_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(node.source, asset_target)
    except OSError as exc:
        error(f"Cannot copy {node.source} to {asset_target}: {exc}")


def _sync_target(target: Path, expected_paths: set[Path]) -> None:
    if not target.exists():
        return

    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_file() and path not in expected_paths:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
