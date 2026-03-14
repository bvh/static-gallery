# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static Gallery is a Python CLI tool that generates static sites and image galleries from directory structures. It recursively scans a source directory, classifies files (markdown, images, static assets), and builds a node tree for site generation. Jinja2 templates in `theme/` render the output.

## Commands

```bash
uv run gallery --help              # CLI help
uv run gallery site/               # Generate site from source directory
uv run pytest                      # Run test suite
uv run pytest tests/test_scanner.py::test_name  # Run a single test
uv run pre-commit run --all-files  # Run ruff linting and formatting checks
```

## Architecture

**Entry point:** `src/static_gallery/__init__.py` delegates to `cli.main()`.

**Data flow:** CLI args → `StaticGalleryConfig` → `Scanner(config).scan(path)` builds a recursive `StaticGalleryNode` tree → `StaticGalleryBuilder(config).render(root, path)` walks the tree, renders Jinja2 templates, writes HTML and copies assets to `public_path`.

**Key modules:**
- `cli.py` — argparse-based CLI with optional flags (`--title`, `--language`, `--url`, `--config`, `--theme`, `--public`). Builds a `StaticGalleryConfig`, scans source, and renders via `StaticGalleryBuilder`.
- `config.py` — `StaticGalleryConfig` class with layered precedence: CLI args > env vars > config file > inferred > defaults. Parses `site.conf` files (`key: value` format). Env vars prefixed `STATIC_GALLERY_*` are mapped to config keys.
- `scanner.py` — `Scanner` class that recursively walks directories, classifies files by extension, creates node tree. `index.md` becomes parent container text (not a separate node). `site.conf` at the root is loaded into config (not a separate node). Directories with only images become GALLERY type; mixed content becomes DIRECTORY.
- `nodes.py` — `StaticGalleryNode` class with typed child collections (`pages`, `images`, `assets`, `dirs`). Node types: HOME, DIRECTORY, GALLERY, MARKDOWN, IMAGE, STATIC.
- `markdown.py` — `MarkdownRenderer` class wrapping `markdown-it-py`. Single `MarkdownIt` instance reused across calls. `render()` supports `extract_title` (pull first H1 as title) and `remove_title` (strip first H1 from output). `render_file()` is the file-based convenience wrapper. Returns `MarkdownResult(html, title)`.
- `builder.py` — `StaticGalleryBuilder` class that walks the node tree, renders each node through Jinja2 templates, writes HTML to `public_path`, and copies images/assets. Template selection: `_default.html` for MARKDOWN/HOME/DIRECTORY-with-index, `_directory.html` for DIRECTORY-without-index, `_gallery.html` for GALLERY. Theme assets (non-underscore-prefixed files) are copied to public root.

**Themes:** `theme/default/` contains Jinja2 templates (`_default.html`, `_directory.html`, `_gallery.html`). Templates receive `site` (dict from config) and `page` (title, content, images, pages, dirs) variables. Content is marked as `Markup` for autoescape. Non-template files (no `_` prefix) are copied as static assets.

## Build & Environment

- Python 3.14, managed with uv
- Build backend: `uv_build`
- Runtime dependencies: `markdown-it-py`, `jinja2`
- Dev dependencies: pytest, pre-commit
- Pre-commit hooks: ruff-check and ruff-format (astral-sh/ruff-pre-commit)

## Development Practices

- Prefer red/green TDD: write failing tests first, then implement to make them pass.
