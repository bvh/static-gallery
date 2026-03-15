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
made available in templates. Each image gets its own page at a pretty URL
(`photo/index.html`) with the image file co-located (`photo/photo.jpg`). If a
markdown file shares the same stem as an image (e.g., `sunset.md` for
`sunset.jpg`), it provides the title and content for that image's page instead
of becoming a standalone page. In gallery and directory templates, each image
dict includes metadata fields alongside `name`, `url` (link to image page),
and `src` (path to image file):

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

Example gallery template usage:
```html
{% for img in page.images %}
  <figure>
    <a href="{{ img.url }}"><img src="{{ img.src }}" alt="{{ img.alt_text or img.name }}"></a>
    <figcaption>
      {{ img.title }}
      {% if img.camera %}Shot on {{ img.camera }}{% endif %}
    </figcaption>
  </figure>
{% endfor %}
```

On individual image pages, the image is available as `page.image`:
```html
<img src="{{ page.image.url }}" alt="{{ page.image.alt_text or page.image.name }}">
{{ page.content }}
```

### Shortcodes

Shortcodes are special tags in markdown content that expand into HTML during
rendering. They use `<<…>>` syntax.

**Embed shortcodes** reference files by their source-relative path (starting
with `/`):

| Syntax | Result |
|--------|--------|
| `<</photos/sunset.jpg>>` | `<img>` tag linking to the image file |
| `<</src/app.py>>` | `<pre><code>` block with the file contents (for known code extensions) |
| `<</files/data.csv>>` | `<a>` link to the file |

**Named shortcodes** invoke built-in functions:

| Syntax | Result |
|--------|--------|
| `<<gallery>>` | Renders the current node's images using the `codes/gallery.html` template |
| `<<gallery sort=datetime>>` | Sorts images by a metadata field |
| `<<gallery sort=datetime reverse>>` | Sorts in reverse order |
| `<<gallery filter="*.jpg">>` | Filters images by filename glob pattern |

Custom themes can override the gallery shortcode template by providing a
`codes/gallery.html` file in the theme directory.

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
