# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static Gallery is a Python CLI tool that generates static sites and image galleries from directory structures. It recursively scans a source directory, classifies files (markdown, images, static assets), and builds a node tree for site generation. Jinja2 templates in `theme/` render the output.

## Commands

```bash
uv run gallery --help              # CLI help
uv run gallery site/               # Generate site from source directory
uv run pytest                      # Run test suite
uv run pre-commit run --all-files  # Run ruff linting and formatting checks
```

## Architecture

**Entry point:** `src/static_gallery/__init__.py` delegates to `cli.main()`.

**Data flow:** CLI args → `StaticGalleryConfig` → `Scanner(config).scan(path)` builds a recursive `StaticGalleryNode` tree → serialized to JSON output.

**Key modules:**
- `cli.py` — argparse-based CLI with optional flags (`--title`, `--language`, `--url`, `--config`, `--theme`, `--public`). Builds a `StaticGalleryConfig`, passes it to scanner.
- `config.py` — `StaticGalleryConfig` class with layered precedence: CLI args > env vars > config file > inferred > defaults. Parses `site.conf` files (`key: value` format). Env vars prefixed `STATIC_GALLERY_*` are mapped to config keys.
- `scanner.py` — `Scanner` class that recursively walks directories, classifies files by extension, creates node tree. `index.md` becomes parent container text (not a separate node). `site.conf` at the root is loaded into config (not a separate node). Directories with only images become GALLERY type; mixed content becomes DIRECTORY.
- `nodes.py` — `StaticGalleryNode` class with typed child collections (`pages`, `images`, `assets`, `dirs`). Node types: HOME, DIRECTORY, GALLERY, MARKDOWN, IMAGE, STATIC.

**Themes:** `theme/default/_default.html` is a Jinja2 template referencing `site.*` and `page.*` variables.

## Build & Environment

- Python 3.14, managed with uv
- Build backend: `uv_build`
- No runtime dependencies
- Dev dependencies: pytest, pre-commit
- Pre-commit hooks: ruff-check and ruff-format (astral-sh/ruff-pre-commit)

## Development Practices

- Prefer red/green TDD: write failing tests first, then implement to make them pass.
