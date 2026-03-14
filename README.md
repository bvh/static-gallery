# Static Gallery

Static Gallery is a simple static site and image gallery generator written
in Python. Modern, well-structured HTML/CSS is encouraged and JavaScript is
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

Build and immediately preview with a local HTTP server:
```
uv run gallery site/ --serve
uv run gallery site/ --serve --port 3000
```

### Configuration

Site configuration uses a layered system with the following precedence
(highest to lowest):

1. **CLI arguments** — `--title`, `--language`, `--url`, `--config`, `--theme`, `--public`, `--serve`, `--port`
2. **Environment variables** — `STATIC_GALLERY_SITE_TITLE`, `STATIC_GALLERY_SITE_LANGUAGE`, `STATIC_GALLERY_SITE_URL`, `STATIC_GALLERY_CONFIG`, `STATIC_GALLERY_THEME`, `STATIC_GALLERY_PUBLIC`
3. **Config file** — a `site.conf` file in the source root directory, using `key: value` format
4. **Defaults** — `site.language` defaults to `en-us`

Example `site.conf`:
```
site.title: My Gallery
site.language: en-us
site.url: https://example.com
```

### Image Metadata

EXIF, IPTC, and XMP metadata is automatically extracted from image files and
made available in templates. In gallery and directory templates, each image
dict includes metadata fields alongside `name` and `url`:

| Field | Description |
|-------|-------------|
| `title` | IPTC object name |
| `description` | Image description (EXIF or IPTC caption) |
| `alt_text` | Accessibility text (XMP, falls back to description/title) |
| `artist` | Photographer name |
| `copyright` | Copyright notice |
| `datetime` | Date taken (Python `datetime` object) |
| `shutter` | Shutter speed (e.g., "1/250") |
| `aperture` | Aperture (e.g., "f/2.8") |
| `iso` | ISO sensitivity |
| `focal_length` | Focal length (e.g., "50mm") |
| `focal_length_35` | 35mm equivalent focal length |
| `camera` | Camera model |
| `camera_make` | Camera manufacturer |
| `lens_model` | Lens model |
| `lens_make` | Lens manufacturer |
| `country`, `city`, `location` | IPTC location fields |
| `province_state` (aliases: `state`, `province`) | State/province |
| `gps_latitude`, `gps_longitude` | Decimal GPS coordinates |
| `keywords` | List of keywords |
| `rating` | Star rating |

Example template usage:
```html
{% for img in page.images %}
  <figure>
    <img src="{{ img.url }}" alt="{{ img.alt_text or img.name }}">
    <figcaption>
      {{ img.title }}
      {% if img.camera %}Shot on {{ img.camera }}{% endif %}
    </figcaption>
  </figure>
{% endfor %}
```

## Development

### Tests

Run the test suite with:
```
uv run pytest
```

### Pre-Commit Hooks

After cloning the repository, install the pre-commit hooks:
```
uv run pre-commit install
```
This will enable automatic linting and formatting check on every commit
via [Ruff](https://docs.astral.sh/ruff/).

## Reference

- [CommonMark Spec](https://spec.commonmark.org/)
- [Jinja Documentation](https://jinja.palletsprojects.com/en/stable/)
