from __future__ import annotations

import shutil
from pathlib import Path

import jinja2
import mistletoe

from static_gallery.config import parse_front_matter
from static_gallery.errors import error
from static_gallery.scanner import BuildTask, TaskType


def build(
    tasks: list[BuildTask],
    site_config: dict[str, str],
    source: Path,
    target: Path,
) -> None:
    theme_dir = source / ".theme"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(theme_dir)),
            autoescape=False,
        )
    except Exception as exc:
        error(f"Cannot load templates from {theme_dir}: {exc}")

    expected_paths: set[Path] = set()

    for task in tasks:
        if task.task_type == TaskType.MARKDOWN:
            _build_markdown(task, site_config, env, expected_paths)
        elif task.task_type == TaskType.IMAGE:
            _build_image(task, site_config, env, expected_paths)
        else:
            _build_static(task, expected_paths)

    _sync_target(target, expected_paths)


def _load_template(env: jinja2.Environment, name: str) -> jinja2.Template:
    try:
        return env.get_template(f"{name}.html")
    except jinja2.TemplateNotFound:
        error(f"Missing template: .theme/{name}.html")
    except jinja2.TemplateSyntaxError as exc:
        error(f"Template syntax error in .theme/{name}.html: {exc}")


def _build_markdown(
    task: BuildTask,
    site_config: dict[str, str],
    env: jinja2.Environment,
    expected_paths: set[Path],
) -> None:
    try:
        text = task.source_path.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"Cannot read {task.source_path}: {exc}")

    metadata, body = parse_front_matter(text)
    html_content = mistletoe.markdown(body)

    template_type = metadata.pop("type", "page")
    template = _load_template(env, template_type)

    output = template.render(site=site_config, page=metadata, content=html_content)

    target_path = task.target_paths[0]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        target_path.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {target_path}: {exc}")

    expected_paths.add(target_path)


def _build_image(
    task: BuildTask,
    site_config: dict[str, str],
    env: jinja2.Environment,
    expected_paths: set[Path],
) -> None:
    stem = task.source_path.stem
    title = stem.replace("-", " ").replace("_", " ").title()
    filename = task.source_path.name

    metadata = {"title": title, "src": filename}
    template = _load_template(env, "image")

    output = template.render(site=site_config, page=metadata, content=filename)

    html_path = task.target_paths[0]
    copy_path = task.target_paths[1]

    html_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        html_path.write_text(output, encoding="utf-8")
    except OSError as exc:
        error(f"Cannot write {html_path}: {exc}")

    try:
        shutil.copy2(task.source_path, copy_path)
    except OSError as exc:
        error(f"Cannot copy {task.source_path} to {copy_path}: {exc}")

    expected_paths.add(html_path)
    expected_paths.add(copy_path)


def _build_static(task: BuildTask, expected_paths: set[Path]) -> None:
    target_path = task.target_paths[0]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(task.source_path, target_path)
    except OSError as exc:
        error(f"Cannot copy {task.source_path} to {target_path}: {exc}")

    expected_paths.add(target_path)


def _sync_target(target: Path, expected_paths: set[Path]) -> None:
    if not target.exists():
        return

    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_file() and path not in expected_paths:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
