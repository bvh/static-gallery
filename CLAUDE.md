# CLAUDE.md

## Project Overview

Static Gallery is a static site generator in Python with first-class image/gallery support. It uses Markdown (CommonMark) for content and Jinja templates for output. Early stage (0.1.0) — the README contains the full design spec.

## Development

- **Python 3.14**, managed with **uv**
- Entry point: `src/static_gallery/__init__.py` → CLI command `gallery` (via `static_gallery:main`)
- Runtime dependencies: `jinja2`, `mistletoe`
- Dev dependencies: `pytest`
- Install/run: `uv run gallery`
- Run tests: `uv run pytest`

## Architecture (from design spec in README)

**Two-pass build system:**
1. Scan source tree and build a dependency graph
2. Execute the graph to produce the target tree

**File processing rules:**
- Dotfiles/dotdirs are ignored
- `.md` files → parsed as CommonMark, generate `.html` in target
- Images (`.jpeg`, `.jpg`, `.webp`, `.png`) → generate an `.html` page per image + copy as static asset
- Everything else (`.css`, `.js`, etc.) → copied as static assets
- Markdown takes precedence over images for HTML generation on name collisions

**Templates:** Jinja files in `.theme/` at source root. Selected by type: `.theme/{type}.html`. Defaults: `page` for markdown, `image` for images. Markdown files can override via `Type:` front matter key. Template variables: `site` (config), `page` (metadata), `content` (rendered HTML or image path).

**Configuration:** `site.conf` in source root — split on first colon, trim whitespace, keys are case-insensitive. `#` lines are comments, blank lines ignored. Required keys: title, url, language. Non-recognized keys are passed through.

**Markdown front matter:** Optional header of key:value lines at top of `.md` files, terminated by a blank line. Same parsing rules as config (split on first colon, trim whitespace, case-insensitive keys) except no comment support.

**Target directory:** Syncs on each build — writes new/updated files, removes orphans with no corresponding source. Created if it doesn't exist.

**Error handling:** Strict fail-fast. Any error (missing config, bad front matter, missing template, unreadable/unwritable files) stops the build immediately with a message to stderr.

**CLI flags:** `--source` (default: cwd), `--target` (default: `.public`), `--config` (default: `site.conf` in source root)
