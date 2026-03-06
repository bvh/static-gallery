# Static Gallery

Static Gallery is a simple static site generator written in Python. Images
are supported as first class objects, with built-in gallery support. Modern,
well-structured HTML/CSS is encouraged, and JavaScript is 100% optional.
Supports Markdown for source text, and Jinja templates for output.

## Prerequisites

* [Python 3.14](https://python.org/)
* [uv](https://docs.astral.sh/uv/getting-started/)

## Setup

After cloning the repository, install the pre-commit hooks:

```
uv run pre-commit install
```

This enables automatic linting and formatting checks (via
[ruff](https://docs.astral.sh/ruff/)) on every commit.

## Usage

Static Gallery is a CLI application. Run `uv run gallery --help` from your
command shell of choice to list options. Here are the basics:

`--source`: set the source directory (default is the current working
directory)

`--target`: sets the target directory (default is `.public`)

`--config`: sets the root configuration file (default is `site.conf` in the
root of the source directory)

## Configuration

The root of the site source directory **must** contain a `site.conf` file.
Config files consists of one entry per line, each containing a key and a
value, separated by a colon. Values are split on the first colon only, so
values may contain colons (e.g., URLs). Leading and trailing whitespace is
trimmed from both keys and values. Blank lines are ignored, and lines
beginning with `#` are treated as comments.

```
# Site metadata
title: Brian Van Horne's Home Page
language: en-us
url: https://brianvanhorne.com/
```

Current supported values are:

**Title**: the title of the site
**URL**: the base URL of the site
**Language**: the locale and language code of the site (e.g. "en-us")

Keys are case-insensitive (e.g., "title", "TITLE", and "TiTLe" all map to
the same value).

Non-recognized keys are allowed, and are available to the system for use
in generating target files.

## Markdown Files

The *content* of markdown files will be parsed in accordance with the
CommonMark spec.

For metadata (title, author, date) an optional header will be supported. If
the first line of a markdown file consists of a key/value pair separated
by a colon, the file contains a header, and all contiguous key/value
lines will be parsed as the header, until a blank line is encountered.
Front matter uses the same parsing rules as `site.conf` — split on the
first colon, trim whitespace from keys and values, keys are
case-insensitive — except that comments are not supported in front matter.
For example:

```
Title: My Blog Post
Date: 2026-03-01

This is the *first* line of my blog post.
```

In this trivial example, The first two lines are parsed as header lines,
making "title" and "date" available to the system as page metadata (as with
configuration, keys are case-insensitive), the third line is the header/body
separator, and is discarded, and the fourth line is passed on to the markdown
parser as the content.

## Templates

Templates are [Jinja](https://jinja.palletsprojects.com/en/stable/) files
stored in the `.theme/` directory at the source root. Because `.theme/`
begins with a dot, it is automatically excluded from content processing
by rule #1 in the workflow below.

The template used for a given page is selected by type: the system looks
for `.theme/{type}.html`. Default types are:

* **page** — used for markdown files (i.e., `.theme/page.html`)
* **image** — used for image files (i.e., `.theme/image.html`)

Markdown files can override the default type via a `Type:` front matter
key. For example, a markdown file with `Type: image` will use
`.theme/image.html` instead of `.theme/page.html`.

The following variables are available within templates:

* **site** — all key/value pairs from `site.conf`
* **page** — page metadata from front matter (markdown files) or generated
  metadata (image files)
* **content** — the rendered HTML body (for markdown files) or the image
  path (for image files)

## Shortcodes

Shortcodes embed content directly into markdown using `<< >>` syntax. They
are expanded before markdown parsing, and each type is rendered through a
Jinja template in `.theme/shortcodes/`.

### File Shortcodes

Reference a file by path to embed it. The file extension determines which
template is used:

```
<<photo.jpg>>                        # image shortcode
<<photo.jpg A beautiful sunset>>     # with explicit alt text
<<code/example.py>>                  # code shortcode (inlined)
<<data.csv>>                         # csv shortcode (inlined)
<<notes.txt>>                        # text shortcode (inlined)
```

Supported types and their templates:

* **image** (`.jpeg`, `.jpg`, `.webp`, `.png`, `.gif`, `.svg`) →
  `.theme/shortcodes/image.html`
* **code** (`.py`, `.js`, `.ts`, `.css`, `.html`, `.sh`, `.json`, `.yaml`,
  `.yml`, `.toml`, `.xml`, `.sql`, `.rs`, `.go`, `.c`, `.h`) →
  `.theme/shortcodes/code.html`
* **text** (`.txt`) → `.theme/shortcodes/text.html`
* **csv** (`.csv`) → `.theme/shortcodes/csv.html`

For images, the alt text defaults to the filename stem with dashes and
underscores replaced by spaces. Code, text, and csv files have their
content inlined into the template.

### Gallery Shortcode

The `<<gallery>>` shortcode embeds a listing of images from a directory,
with each image linking to its generated HTML page:

```
<<gallery>>                              # all images in current directory
<<gallery sort=name>>                    # sorted by filename (default)
<<gallery sort=date reverse>>            # reverse chronological
<<gallery filter=*.jpg>>                 # only JPGs
<<gallery path=photos>>                  # images from a subdirectory
<<gallery path=photos sort=name filter=*.jpg>>
```

| Option    | Values         | Default     | Description                      |
|-----------|----------------|-------------|----------------------------------|
| `sort`    | `name`, `date` | `name`      | Sort key                         |
| `reverse` | bare flag      | false       | Reverse sort order               |
| `filter`  | glob pattern   | none        | Filter filenames (e.g. `*.jpg`)  |
| `path`    | relative path  | current dir | Directory to scan                |

The gallery is rendered through `.theme/shortcodes/gallery.html`, which
receives an `images` list (each with `path`, `filename`, `stem`,
`extension`, `alt`, and `page_url`) and an `options` dict.

Only image types that generate HTML pages (`.jpeg`, `.jpg`, `.webp`,
`.png`) are included in gallery listings.

## Workflow

The system starts by scanning the root of the site source directory for a
`site.conf` and parsing it. If one is not found, or if the file cannot be
parsed, it will exit with an error.

The target directory is created if it doesn't exist. On each build, the
system syncs the target with the source: it writes new and updated files,
and removes any files in the target that no longer correspond to a source
file. This prevents stale files from accumulating across builds.

Next, scan the directory for any remaining items. We use a two pass system,
so first scan the tree and create a graph of work required to build the site,
and then do the work. Use the following rules:

1. Ignore all files and directories that begin with a dot (`.`).
2. Markdown files (`*.md`) will be processed as content and the resulting
HTML file mapped to a corresponding location in the target tree.
3. Images (`*.jpeg`, `*.jpg`, `*.webp`, `*.png`) will also be processed as
content, by default, creating a single HTML page for each image and mapping
it to the corresponding location in the target tree. The image itself will
also be mapped to the target tree in the same location.
4. Static assets (`*.css`, `*.js`, and anything else) will be mapped directly
over to the corresponding location in the target tree.

### Precedence and Name Collisions

In generating HTML pages, markdown files take precedence over images. For
example, if both `about.md` and `about.jpg` exist in the same source
directory, `about.html` in the target directory will be generated by the
contents of `about.md` and `about.jpg` is simply treated as a static asset.

### A Simple Example

Given the following source tree:
```
├── site.conf
├── index.md
├── about.md
├── portrait.jpg
├── news
│   ├── index.md
│   ├── today.md
│   └── today.jpg
└── styles.css
```

First, the system will locate `site.conf` and parse it.

Next, it will scan through the remaining files:

* `index.md` will be used to generate `index.html` in the target tree
* `about.md` will be used to generate `about.html` in the target tree
* `portrait.jpg` will be used to generate `portrait.html` in the target tree
**and** will also be copied over as a static asset to `portrait.jpg`
* `news` is a directory, so the system will recursively scan it:
  * `news/index.md` will be parsed and mapped to `news/index.html`
  * `news/today.md` will be parsed and mapped to `news/today.html`
  * `news/today.jpg` conflicts with `today.md` and will not generate an HTML
  file, but will still be copied as an asset to `news/today.jpg` in the target
  tree
* `styles.css` is a static asset, and will simply be copied over to
`styles.css` in the target tree with no parsing

The resulting target tree should look like this:

```
├── index.html      <-- generated from index.md
├── about.html      <-- generated from about.md
├── portrait.html   <-- generated from portrait.jpg
├── portrait.jpg    <-- copied from portrait.jpg
├── news
│   ├── index.html  <-- generated from news/index.md
│   ├── today.html  <-- generated from news/today.md
│   └── today.jpg   <-- copied from news/today.jpg
└── styles.css      <-- copied from styles.css
```

## Error Handling

The system uses strict fail-fast behavior. Any error stops the build
immediately and reports a clear message to stderr. This includes, but is
not limited to: a missing or unparseable `site.conf`, invalid front matter,
a missing template, an unreadable source file, or an unwritable target
directory.

## References

* [Jinja Documentation](https://jinja.palletsprojects.com/en/stable/)
* [CommonMark Spec](https://spec.commonmark.org/)
