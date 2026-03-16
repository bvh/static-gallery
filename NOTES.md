# MISCELLANEOUS NOTES

## Setup for Web Site Use

### Create a Bare UV Project
```
uv init --bare brianvanhorne.com
cd brianvanhorne.com
```

### Install Static Gallery from GitHub
```
uv add git+ssh://git@github.com/bvh/static-gallery
uv run gallery --help
```

### Update Static Gallery
```
uv add --upgrade static-gallery
uv run gallery --help
```

### Build Site and Run Staging Server
```
uv run gallery site --serve
open http://localhost:8000/
```
This will build the site to public/ and serve it via the build in
staging server.


## Project Initialization

### Create the GitHub Repository

The initial `README.md`, `.gitignore`, etc. will be created by `uv`. To prevent
potential conflicts, **DO NOT** create them when creating the GitHub repository.

- https://github.com/new
    - General:
        - Owner: `bvh`
        - Repository name: `static-gallery`
        - Description: `Simple static site and image gallery generator written in Python`
    - Configuration:
        - Choose visibility: `Public`
        - Add README: `Off`
        - Add .gitignore: `No .gitignore`
        - Add license: `No license`
    - Jumpstart your project with Copilot (optional)
        - Prompt: *(leave blank)*

### Initialize the UV Project

```
uv self update
uv init --app --package static-gallery
cd static-gallery
```

### Initial Edits

```
touch DESIGN.md
touch NOTES.md
```

Edit `pyproject.toml`:
- Under `[project]`, update the `description`.
- Under `[project.scripts]`, change `static-gallery` to `gallery`.

Edit `README.md`:
- Add description, prerequisites, and basic installation and usage info.

### Commit to LOCAL Repository

```
git status
git add .
git status
git commit -m "initial commit"
```

### Set Origin and Push to GitHub

```
git remote add origin git@github.com:bvh/static-gallery.git
git branch -M main
git push -u origin main
```

### Install/Update Ruff

```
ruff version
which ruff
uv tool install ruff@latest
ruff version
which ruff
ruff help
ruff check .
ruff format .
```

### Add Ruff Pre-Commit Hook

#### Install Pre-Commit Package
Install `pre-commit` as a development dependency:
```
uv add --dev pre-commit
touch .pre-commit-config.yaml
```

#### Configure Pre-Commit Hooks
Add the following to `.pre-commit-config.yaml`:
```
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  # ruff version:
  rev: v0.15.6
  hooks:
    - id: ruff-check
    - id: ruff-format
```
Change the `rev: v0.15.6` line to match the current version of `ruff`
(run `ruff version`).

#### Install Hooks and Verify
Install the pre-commit scripts into `.git/hooks` and verify:
```
uv run pre-commit install
uv run pre-commit run --all-files
```
