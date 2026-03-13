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

Run the `gallery` command, supplying both a source directory and a target
directory. Use the `--help` command argument for more details.
```
uv run gallery --help
uv run gallery site/ public/
```

## Reference

- [CommonMark Spec](https://spec.commonmark.org/)
- [Jinja Documentation](https://jinja.palletsprojects.com/en/stable/)
