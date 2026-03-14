import logging
import re
from datetime import datetime
from fractions import Fraction

import pyexiv2

logger = logging.getLogger(__name__)

FIELDS = (
    "title",
    "description",
    "alt_text",
    "artist",
    "copyright",
    "datetime",
    "shutter",
    "aperture",
    "iso",
    "focal_length",
    "focal_length_35",
    "camera",
    "camera_make",
    "lens",
    "lens_model",
    "lens_make",
    "country_code",
    "country",
    "province_state",
    "city",
    "location",
    "gps_latitude",
    "gps_longitude",
    "keywords",
    "rating",
    "state",
    "province",
)


def _get(data, key, default=None):
    """Get a value from a metadata dict, returning default if absent or empty."""
    val = data.get(key)
    if val is None or val == "":
        return default
    return val


def _parse_rational(value):
    """Parse an Exiv2 rational value like '50/1' to a Fraction."""
    try:
        return Fraction(value)
    except ValueError, ZeroDivisionError:
        return None


def _parse_gps_coordinate(dms_string, ref):
    """Convert GPS DMS string (e.g. '48/1 51/1 24/1') and ref ('N'/'S'/'E'/'W') to decimal degrees."""
    if not dms_string or not ref:
        return None
    parts = dms_string.strip().split()
    if len(parts) != 3:
        return None
    try:
        degrees = Fraction(parts[0])
        minutes = Fraction(parts[1])
        seconds = Fraction(parts[2])
    except ValueError, ZeroDivisionError:
        return None
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def _parse_exif_datetime(s):
    """Parse EXIF datetime string 'YYYY:MM:DD HH:MM:SS' to datetime object."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _parse_iptc_datetime(date_str, time_str):
    """Parse IPTC DateCreated + TimeCreated to datetime object."""
    if not date_str:
        return None
    try:
        date_part = date_str.strip()
        if time_str:
            # Strip timezone offset if present (e.g. +00:00)
            time_clean = re.sub(r"[+-]\d{2}:\d{2}$", "", time_str.strip())
            return datetime.strptime(f"{date_part} {time_clean}", "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(date_part, "%Y-%m-%d")
    except ValueError:
        return None


def _format_shutter(value):
    """Format exposure time as human-readable string like '1/250'."""
    if not value:
        return None
    frac = _parse_rational(value)
    if frac is None:
        return value
    if frac >= 1:
        secs = float(frac)
        return f"{secs:g}s" if secs != int(secs) else f"{int(secs)}s"
    return str(frac)


def _format_aperture(value):
    """Format f-number as 'f/2.8'."""
    if not value:
        return None
    frac = _parse_rational(value)
    if frac is None:
        return value
    f = float(frac)
    if f == int(f):
        return f"f/{int(f)}"
    return f"f/{f:g}"


def _format_focal_length(value):
    """Format focal length as '50mm'."""
    if not value:
        return None
    frac = _parse_rational(value)
    if frac is not None:
        f = float(frac)
        if f == int(f):
            return f"{int(f)}mm"
        return f"{f:g}mm"
    # Might already be a plain number string
    try:
        f = float(value)
        if f == int(f):
            return f"{int(f)}mm"
        return f"{f:g}mm"
    except ValueError:
        return value


def read_metadata(path):
    """Read EXIF, IPTC, and XMP metadata from an image file.

    Returns a dict of human-readable metadata fields. Missing fields are None.
    """
    try:
        img = pyexiv2.Image(path)
        try:
            exif = img.read_exif()
            iptc = img.read_iptc()
            xmp = img.read_xmp()
        finally:
            img.close()
    except Exception:
        logger.debug("Failed to read metadata from %s", path, exc_info=True)
        return _empty_metadata()

    title = _get(iptc, "Iptc.Application2.ObjectName")
    description = _get(exif, "Exif.Image.ImageDescription") or _get(
        iptc, "Iptc.Application2.Caption"
    )

    # alt_text: XMP AltTextAccessibility → description → title
    alt_text = _get(xmp, "Xmp.iptcExt.AltTextAccessibility")
    if alt_text is None:
        alt_text = description if description else title

    artist = _get(exif, "Exif.Image.Artist") or _get(iptc, "Iptc.Application2.Byline")
    copyright_ = _get(exif, "Exif.Image.Copyright") or _get(
        iptc, "Iptc.Application2.Copyright"
    )

    # datetime
    dt = _parse_exif_datetime(_get(exif, "Exif.Photo.DateTimeOriginal"))
    if dt is None:
        dt = _parse_iptc_datetime(
            _get(iptc, "Iptc.Application2.DateCreated"),
            _get(iptc, "Iptc.Application2.TimeCreated"),
        )

    # Exposure
    shutter = _format_shutter(_get(exif, "Exif.Photo.ExposureTime"))
    if shutter is None:
        shutter = _format_shutter(_get(exif, "Exif.Photo.ShutterSpeedValue"))
    aperture = _format_aperture(_get(exif, "Exif.Photo.FNumber"))
    if aperture is None:
        aperture = _format_aperture(_get(exif, "Exif.Photo.ApertureValue"))
    iso = _get(exif, "Exif.Photo.ISOSpeedRatings")

    # Focal length
    focal_length = _format_focal_length(_get(exif, "Exif.Photo.FocalLength"))
    focal_length_35 = _format_focal_length(
        _get(exif, "Exif.Photo.FocalLengthIn35mmFilm")
    )

    # Camera/lens
    camera = _get(exif, "Exif.Image.Model")
    camera_make = _get(exif, "Exif.Image.Make")
    lens = _get(exif, "Exif.Photo.LensSpecification")
    lens_model = _get(exif, "Exif.Photo.LensModel")
    lens_make = _get(exif, "Exif.Photo.LensMake")

    # Location (IPTC)
    country_code = _get(iptc, "Iptc.Application2.CountryCode")
    country = _get(iptc, "Iptc.Application2.CountryName")
    province_state = _get(iptc, "Iptc.Application2.ProvinceState")
    city = _get(iptc, "Iptc.Application2.City")
    location = _get(iptc, "Iptc.Application2.SubLocation")

    # GPS
    gps_latitude = _parse_gps_coordinate(
        _get(exif, "Exif.GPSInfo.GPSLatitude"),
        _get(exif, "Exif.GPSInfo.GPSLatitudeRef"),
    )
    gps_longitude = _parse_gps_coordinate(
        _get(exif, "Exif.GPSInfo.GPSLongitude"),
        _get(exif, "Exif.GPSInfo.GPSLongitudeRef"),
    )

    # Keywords
    keywords = _get(iptc, "Iptc.Application2.Keywords")
    if keywords is None:
        keywords = _get(xmp, "Xmp.dc.subject")

    # Rating
    rating = _get(xmp, "Xmp.xmp.Rating")

    return {
        "title": title,
        "description": description,
        "alt_text": alt_text,
        "artist": artist,
        "copyright": copyright_,
        "datetime": dt,
        "shutter": shutter,
        "aperture": aperture,
        "iso": iso,
        "focal_length": focal_length,
        "focal_length_35": focal_length_35,
        "camera": camera,
        "camera_make": camera_make,
        "lens": lens,
        "lens_model": lens_model,
        "lens_make": lens_make,
        "country_code": country_code,
        "country": country,
        "province_state": province_state,
        "city": city,
        "location": location,
        "gps_latitude": gps_latitude,
        "gps_longitude": gps_longitude,
        "keywords": keywords,
        "rating": rating,
        # Aliases
        "state": province_state,
        "province": province_state,
    }


def _empty_metadata():
    """Return a metadata dict with all fields set to None."""
    return {f: None for f in FIELDS}
