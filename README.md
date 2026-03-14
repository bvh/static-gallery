# Static Gallery

Static Gallery is a simple static site and image gallery generator written
in Python. Modern, well-structures HTML/CSS is encourages and JavaScript is
100% optional.

## Getting Started

### Prerequisites

- This has been built and tested with [Python 3.14](https://python.org/).
- I use [uv](https://docs.astral.sh/uv/getting-started/) for package
and runtime management. You should too.
- There is currently no installation package, so `git` is required to clone
and install the package.
- As this is a command line (CLI) application, basic familiarity with your
command shell of choice is recommended.

### Installation

Clone the GitHub repository:
```
git clone git@github.com:bvh/static-gallery.git
cd static-gallery
uv run gallery --help
```

### Usage

Run the `gallery` command, supplying a source directory. Use the `--help`
command argument for more details.
```
uv run gallery --help
uv run gallery site/
```

Optional flags allow overriding configuration:
```
uv run gallery site/ --title "My Site" --language en-us --url https://example.com
uv run gallery site/ --config path/to/site.conf --theme path/to/theme --public path/to/output
```

### Configuration

Site configuration uses a layered system with the following precedence
(highest to lowest):

1. **CLI arguments** — `--title`, `--language`, `--url`, `--config`, `--theme`, `--public`
2. **Environment variables** — `STATIC_GALLERY_SITE_TITLE`, `STATIC_GALLERY_SITE_LANGUAGE`, `STATIC_GALLERY_SITE_URL`, `STATIC_GALLERY_CONFIG`, `STATIC_GALLERY_THEME`, `STATIC_GALLERY_PUBLIC`
3. **Config file** — a `site.conf` file in the source root directory, using `key: value` format
4. **Defaults** — `site.language` defaults to `en-us`

Example `site.conf`:
```
site.title: My Gallery
site.language: en-us
site.url: https://example.com
```

## Development

### Tests

Run the test suite with:
```
uv run pytest
```

### Pre-Commit Hooks

After cloning the reepository, install the pre-commit hooks:
```
uv run pre-commit install
```
This will enable automatic linting and formatting check on every commit
via [Ruff](https://docs.astral.sh/ruff/).

## Reference

- [CommonMark Spec](https://spec.commonmark.org/)
- [Jinja Documentation](https://jinja.palletsprojects.com/en/stable/)
