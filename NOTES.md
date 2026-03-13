# MISCELLANEOUS NOTES

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
