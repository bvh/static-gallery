# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static Gallery is a Python CLI tool that generates static sites and image galleries from directory structures. It recursively scans a source directory, classifies files (markdown, images, static assets), and builds a node tree for site generation. Jinja2 templates bundled with the package render the output.

## Commands

```bash
uv run gallery --help              # CLI help
uv run gallery example/            # Generate site from source directory
uv run pytest                      # Run test suite
uv run pytest tests/test_scanner.py::test_name  # Run a single test
uv run pre-commit run --all-files  # Run ruff linting and formatting checks
```

## Architecture

**Entry point:** `src/static_gallery/__init__.py` delegates to `cli.main()`.

**Data flow:** CLI args → `Config` → `Scanner(config).scan(path)` builds a recursive `Node` tree → `Builder(config).render(root, path)` walks the tree, renders Jinja2 templates, writes HTML and copies assets to `public_path`.

**Key modules:**
- `cli.py` — argparse-based CLI with optional flags (`--title`, `--language`, `--url`, `--config`, `--theme`, `--public`, `--serve`, `--port`). Builds a `Config`, scans source, and renders via `Builder`. `--serve` starts a local HTTP server after build; `--port` sets the port (default 8000). These flags are CLI-only behavior, not site configuration.
- `config.py` — `Config` class with layered precedence: CLI args > env vars > config file > inferred > defaults. Parses `site.conf` files (`key: value` format). Env vars prefixed `STATIC_GALLERY_*` are mapped to config keys.
- `scanner.py` — `Scanner` class that recursively walks directories, classifies files by extension, creates node tree. Uses a two-phase scan: first collects all entries, then pairs markdown files with images by stem (`photo.md` + `photo.jpg` → paired). Paired markdown sets `content_path` on the IMAGE node instead of creating a MARKDOWN node, preserving gallery classification. `index.md` becomes parent container text (not a separate node). `site.conf` at the root is loaded into config (not a separate node). Directories with only images (including those with paired markdown) become GALLERY type; mixed content becomes DIRECTORY.
- `node.py` — `Node` class with typed child collections (`pages`, `images`, `assets`, `dirs`). Node types: HOME, DIRECTORY, GALLERY, MARKDOWN, IMAGE, STATIC. IMAGE nodes have a lazy `metadata` property that reads EXIF/IPTC/XMP data on first access and an optional `content_path` for paired markdown. `index_path` stores the path to an `index.md` file for container nodes. `template_name` property returns the appropriate template (`image.html`, `gallery.html`, `directory.html`, or `default.html`). `title_fallback` property returns `stem` for MARKDOWN and IMAGE nodes, `name` for others.
- `markdown.py` — `MarkdownRenderer` class wrapping `markdown-it-py`. Single `MarkdownIt` instance reused across calls. `render()` supports `extract_title` (pull first H1 as title) and `remove_title` (strip first H1 from output). `render_file()` is the file-based convenience wrapper. Returns `MarkdownResult(html, title)`.
- `metadata.py` — `read_metadata(path)` function that reads EXIF/IPTC/XMP metadata from image files using pyexiv2. Returns a dict of human-readable fields (title, description, camera settings, GPS, keywords, etc.). Called lazily via `Node.metadata` property.
- `builder.py` — `Builder` class that walks the node tree, renders each node through Jinja2 templates, writes HTML to `public_path`, and copies assets. Each IMAGE node gets its own page at `stem/index.html` with the image file co-located at `stem/name`. For IMAGE nodes, `page.image` provides a dict with `url` (sibling filename), `name`, and all metadata fields. For parent nodes listing images, `img.url` links to the image page (`stem/`) and `img.src` points to the image file (`stem/name`). Paired markdown content (via `content_path`) provides title and body for image pages. Template selection and title fallback logic are delegated to `Node.template_name` and `Node.title_fallback` properties. Files in the theme's `static/` subdirectory are copied to the public root.

**Themes:** `src/static_gallery/themes/default/` contains the bundled default Jinja2 templates (`default.html`, `directory.html`, `gallery.html`, `image.html`), loaded via `PackageLoader`. Templates receive `site` (dict from config), `page` (title, content, images, pages, dirs), and `generator` (name, package, version) variables. `generator.name` is a human-readable title-cased name (e.g. "Static Gallery"), `generator.package` is the raw package name, and `generator.version` is the version string. Content is marked as `Markup` for autoescape. The `image.html` template renders individual image pages with `page.image` (url, name, metadata) and optional `page.content` from paired markdown. In `gallery.html`, `img.url` links to the image page and `img.src` is the thumbnail file path. Static assets live in a `static/` subdirectory within the theme and are copied to the public root (preserving subdirectory structure). Custom themes use `FileSystemLoader` via `--theme`.

## Build & Environment

- Python 3.14, managed with uv
- Build backend: `uv_build`
- Runtime dependencies: `markdown-it-py`, `jinja2`, `pyexiv2`
- Dev dependencies: pytest, pre-commit
- Pre-commit hooks: ruff-check and ruff-format (astral-sh/ruff-pre-commit)

## Example Images

SVG sources live in `images/`. Run `images/generate.sh` to generate raster images
for the `example/` directory. Requires `rsvg-convert` (librsvg), ImageMagick (`magick`),
and `exiftool`. Install with: `brew install librsvg imagemagick exiftool`.

## Development Practices

- Prefer red/green TDD: write failing tests first, then implement to make them pass.
