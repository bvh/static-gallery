# Suggestions for Improvement

## Bugs



## Design

### ~~Shortcode type map is a maintenance burden~~ (done)

Replaced `_SHORTCODE_TYPE_MAP` and `_LANGUAGE_MAP` with `_shortcode_type()` and `_language_for()` functions. Image extensions come from `IMAGE_EXTENSIONS`, `.txt`/`.csv` are explicit, and everything else falls back to "code". Language is derived from the extension with a small override map for names that differ (e.g. `.py` → `python`).

### The builder does too much

Template loading, markdown rendering, image processing, static copying, listing generation, metadata extraction, and target sync are all in one module. The sync logic in particular is independent — it could be its own function called from `main()` after `build()`, which would make the separation between "generate files" and "clean up stale files" explicit in the orchestration.

## Testing

