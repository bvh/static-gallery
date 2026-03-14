# Known Issues

## Default theme path is fragile

The `Renderer` resolves the bundled default theme via a relative path from `__file__` (`../../theme/default`). This works in a development checkout but will break if the package is installed normally (e.g. via `pip install` or `uv pip install`), because the `theme/` directory sits outside the package and won't be included in the installed distribution.

**Possible fixes:**
- Use `importlib.resources` to locate theme files bundled inside the package.
- Add `theme/` to the package data in `pyproject.toml` and restructure so it lives under `src/static_gallery/`.
