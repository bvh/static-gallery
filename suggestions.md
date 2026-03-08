# Suggestions for Improvement

## Bugs



## Design

### The builder does too much

Template loading, markdown rendering, image processing, static copying, listing generation, metadata extraction, and target sync are all in one module. The sync logic in particular is independent — it could be its own function called from `main()` after `build()`, which would make the separation between "generate files" and "clean up stale files" explicit in the orchestration.

## Testing

