from __future__ import annotations

import sys
from pathlib import Path

import pyexiv2


def _shorten_key(key: str) -> str:
    """Strip the two-segment namespace prefix, keeping the rest.

    Examples:
        "Iptc.Application2.ObjectName" → "ObjectName"
        "Xmp.dc.title" → "title"
        "Xmp.crs.FilterList/crs:Filters[1]/crs:Title" → "FilterList/crs:Filters[1]/crs:Title"
    """
    parts = key.split(".", 2)
    if len(parts) == 3:
        return parts[2]
    return key


def _extract_lang_alt(value: object) -> str | None:
    """Extract the default language string from an XMP lang-alt dict."""
    if isinstance(value, dict):
        return value.get('lang="x-default"')
    return None


def read_image_metadata(path: Path) -> dict[str, dict]:
    """Read EXIF, IPTC, and XMP metadata from an image file.

    Returns {"exif": {...}, "iptc": {...}, "xmp": {...}} with shortened keys.
    On failure, returns empty dicts — metadata is supplemental.
    """
    result: dict[str, dict] = {"exif": {}, "iptc": {}, "xmp": {}}
    try:
        img = pyexiv2.Image(str(path))
        try:
            for category, reader in [
                ("exif", img.read_exif),
                ("iptc", img.read_iptc),
                ("xmp", img.read_xmp),
            ]:
                raw = reader()
                result[category] = {_shorten_key(k): v for k, v in raw.items()}
        finally:
            img.close()
    except Exception as exc:
        print(f"Warning: could not read metadata from {path}: {exc}", file=sys.stderr)
    return result


def resolve_title(stem: str, metadata: dict[str, dict]) -> str:
    """Determine image title from metadata, falling back to filename stem."""
    iptc_title = metadata.get("iptc", {}).get("ObjectName")
    if iptc_title:
        return iptc_title

    xmp_title = metadata.get("xmp", {}).get("title")
    if xmp_title:
        extracted = _extract_lang_alt(xmp_title)
        if extracted:
            return extracted

    return stem.replace("-", " ").replace("_", " ").title()


def resolve_alt(stem: str, metadata: dict[str, dict]) -> str:
    """Determine alt text from metadata, falling back to filename stem."""
    xmp_alt = metadata.get("xmp", {}).get("AltTextAccessibility")
    if xmp_alt:
        extracted = _extract_lang_alt(xmp_alt)
        if extracted:
            return extracted

    return stem.replace("-", " ").replace("_", " ")
