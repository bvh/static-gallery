from __future__ import annotations


class GalleryError(Exception):
    pass


def error(msg: str) -> None:
    raise GalleryError(msg)
