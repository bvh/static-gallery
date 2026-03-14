import os

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove STATIC_GALLERY_* env vars so tests don't depend on the host."""
    for key in list(os.environ):
        if key.startswith("STATIC_GALLERY_"):
            monkeypatch.delenv(key)
