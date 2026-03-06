from __future__ import annotations

import shutil
from pathlib import Path

import jinja2
from markupsafe import Markup
import mistletoe

from static_gallery.config import parse_front_matter
from static_gallery.errors import error
from static_gallery.model import FileType, SourceDir, SourceFile, all_target_paths


def build(
    tree: SourceDir,
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

    _build_dir(tree, site_config, env)
    _sync_target(target, all_target_paths(tree))


def _build_dir(
    node: SourceDir,
    site_config: dict[str, str],
    env: jinja2.Environment,
) -> None:
    for f in node.files:
        if f.file_type == FileType.MARKDOWN:
            _build_markdown(f, site_config, env)
        elif f.file_type == FileType.IMAGE:
            _build_image(f, site_config, env)
        else:
            _build_static(f)
    for child in node.children.values():
        _build_dir(child, site_config, env)


def _load_template(env: jinja2.Environment, name: str) -> jinja2.Template:
    try:
        return env.get_template(f"{name}.html")
    except jinja2.TemplateNotFound:
        error(f"Missing template: .theme/{name}.html")
    except jinja2.TemplateSyntaxError as exc:
        error(f"Template syntax error in .theme/{name}.html: {exc}")


def _build_markdown(
    f: SourceFile,
    site_config: dict[str, str],
    env: jinja2.Environment,
) -> None:
    try:
        text = f.source_path.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"Cannot read {f.source_path}: {exc}")

    metadata, body = parse_front_matter(text)
    html_content = mistletoe.markdown(body)

    template_type = metadata.get("type", "page")
    if "type" in metadata:
        del metadata["type"]
    template = _load_template(env, template_type)

    output = template.render(site=site_config, page=metadata, content=Markup(html_content))

    f.html_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        f.html_target.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {f.html_target}: {exc}")


def _build_image(
    f: SourceFile,
    site_config: dict[str, str],
    env: jinja2.Environment,
) -> None:
    stem = f.source_path.stem
    title = stem.replace("-", " ").replace("_", " ").title()
    filename = f.source_path.name

    metadata = {"title": title, "src": filename}
    template = _load_template(env, "image")

    output = template.render(site=site_config, page=metadata, content=filename)

    f.html_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        f.html_target.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {f.html_target}: {exc}")

    try:
        shutil.copy2(f.source_path, f.asset_target)
    except OSError as exc:
        error(f"Cannot copy {f.source_path} to {f.asset_target}: {exc}")


def _build_static(f: SourceFile) -> None:
    f.asset_target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(f.source_path, f.asset_target)
    except OSError as exc:
        error(f"Cannot copy {f.source_path} to {f.asset_target}: {exc}")


def _sync_target(target: Path, expected_paths: set[Path]) -> None:
    if not target.exists():
        return

    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_file() and path not in expected_paths:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
