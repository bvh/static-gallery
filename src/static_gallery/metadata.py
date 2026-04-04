import logging
import mimetypes
import os
import re
from datetime import datetime
from fractions import Fraction
from types import SimpleNamespace

import pyexiv2

logger = logging.getLogger(__name__)


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


def _build_file_layer(path):
    """Build the file metadata layer from path and optional pyexiv2 image."""
    stem = os.path.splitext(os.path.basename(path))[0]
    mime_type = mimetypes.guess_type(path)[0]
    try:
        stat = os.stat(path)
        mtime = stat.st_mtime
        ctime = stat.st_ctime
    except OSError:
        mtime = None
        ctime = None

    width = None
    height = None

    return SimpleNamespace(
        name=stem,
        type=mime_type,
        width=width,
        height=height,
        mtime=mtime,
        ctime=ctime,
    )


def _build_exif_layer(exif):
    """Build the raw EXIF metadata layer."""
    return SimpleNamespace(
        description=_get(exif, "Exif.Image.ImageDescription"),
        artist=_get(exif, "Exif.Image.Artist"),
        datetime=_get(exif, "Exif.Photo.DateTimeOriginal"),
        copyright=_get(exif, "Exif.Image.Copyright"),
        shutter_speed=_get(exif, "Exif.Photo.ExposureTime")
        or _get(exif, "Exif.Photo.ShutterSpeedValue"),
        aperture=_get(exif, "Exif.Photo.FNumber")
        or _get(exif, "Exif.Photo.ApertureValue"),
        iso=_get(exif, "Exif.Photo.ISOSpeedRatings"),
        focal_length=_get(exif, "Exif.Photo.FocalLength"),
        focal_length_35=_get(exif, "Exif.Photo.FocalLengthIn35mmFilm"),
        camera=_get(exif, "Exif.Image.Model"),
        camera_make=_get(exif, "Exif.Image.Make"),
        lens_info=_get(exif, "Exif.Photo.LensSpecification"),
        lens=_get(exif, "Exif.Photo.LensModel"),
        lens_make=_get(exif, "Exif.Photo.LensMake"),
        latitude=_get(exif, "Exif.GPSInfo.GPSLatitude"),
        latitude_ref=_get(exif, "Exif.GPSInfo.GPSLatitudeRef"),
        longitude=_get(exif, "Exif.GPSInfo.GPSLongitude"),
        longitude_ref=_get(exif, "Exif.GPSInfo.GPSLongitudeRef"),
    )


def _build_iptc_layer(iptc):
    """Build the raw IPTC metadata layer."""
    return SimpleNamespace(
        name=_get(iptc, "Iptc.Application2.ObjectName"),
        caption=_get(iptc, "Iptc.Application2.Caption"),
        byline=_get(iptc, "Iptc.Application2.Byline"),
        date=_get(iptc, "Iptc.Application2.DateCreated"),
        time=_get(iptc, "Iptc.Application2.TimeCreated"),
        copyright=_get(iptc, "Iptc.Application2.Copyright"),
        country_code=_get(iptc, "Iptc.Application2.CountryCode"),
        country=_get(iptc, "Iptc.Application2.CountryName"),
        province_state=_get(iptc, "Iptc.Application2.ProvinceState"),
        city=_get(iptc, "Iptc.Application2.City"),
        sublocation=_get(iptc, "Iptc.Application2.SubLocation"),
        keywords=_get(iptc, "Iptc.Application2.Keywords"),
    )


def _build_xmp_layer(xmp):
    """Build the raw XMP metadata layer."""
    return SimpleNamespace(
        alt_text=_get(xmp, "Xmp.iptcExt.AltTextAccessibility"),
        subject=_get(xmp, "Xmp.dc.subject"),
        rating=_get(xmp, "Xmp.xmp.Rating"),
    )


def _empty_namespace(fields):
    """Create a SimpleNamespace with all given field names set to None."""
    return SimpleNamespace(**{f: None for f in fields})


_EXIF_FIELDS = (
    "description",
    "artist",
    "datetime",
    "copyright",
    "shutter_speed",
    "aperture",
    "iso",
    "focal_length",
    "focal_length_35",
    "camera",
    "camera_make",
    "lens_info",
    "lens",
    "lens_make",
    "latitude",
    "latitude_ref",
    "longitude",
    "longitude_ref",
)

_IPTC_FIELDS = (
    "name",
    "caption",
    "byline",
    "date",
    "time",
    "copyright",
    "country_code",
    "country",
    "province_state",
    "city",
    "sublocation",
    "keywords",
)

_XMP_FIELDS = ("alt_text", "subject", "rating")

_FILE_FIELDS = ("name", "type", "width", "height", "mtime", "ctime")


DERIVED_FIELDS = (
    "title",
    "description",
    "alt_text",
    "artist",
    "copyright",
    "datetime",
    "camera",
    "camera_make",
    "lens",
    "lens_info",
    "lens_make",
    "shutter",
    "aperture",
    "iso",
    "focal_length",
    "focal_length_35",
    "exposure",
    "sublocation",
    "city",
    "province_state",
    "state",
    "province",
    "country",
    "country_code",
    "location",
    "latitude",
    "longitude",
    "keywords",
    "rating",
)


class Metadata:
    """Structured image metadata with raw layers and derived properties."""

    def __init__(self, file=None, exif=None, iptc=None, xmp=None):
        self.file = file or _empty_namespace(_FILE_FIELDS)
        self.exif = exif or _empty_namespace(_EXIF_FIELDS)
        self.iptc = iptc or _empty_namespace(_IPTC_FIELDS)
        self.xmp = xmp or _empty_namespace(_XMP_FIELDS)

    # --- Derived properties ---

    @property
    def title(self):
        return self.iptc.name or self.file.name

    @property
    def description(self):
        return self.exif.description or self.iptc.caption

    @property
    def alt_text(self):
        return self.xmp.alt_text or self.description or self.title

    @property
    def artist(self):
        return self.exif.artist or self.iptc.byline

    @property
    def copyright(self):
        return self.exif.copyright or self.iptc.copyright

    @property
    def datetime(self):
        dt = _parse_exif_datetime(self.exif.datetime)
        if dt is None:
            dt = _parse_iptc_datetime(self.iptc.date, self.iptc.time)
        if dt is None and self.file.ctime is not None:
            dt = datetime.fromtimestamp(self.file.ctime)
        return dt

    @property
    def camera(self):
        return self.exif.camera

    @property
    def camera_make(self):
        return self.exif.camera_make

    @property
    def lens(self):
        return self.exif.lens

    @property
    def lens_info(self):
        return self.exif.lens_info

    @property
    def lens_make(self):
        return self.exif.lens_make

    @property
    def shutter(self):
        return _format_shutter(self.exif.shutter_speed)

    @property
    def aperture(self):
        return _format_aperture(self.exif.aperture)

    @property
    def iso(self):
        return self.exif.iso

    @property
    def focal_length(self):
        return _format_focal_length(self.exif.focal_length)

    @property
    def focal_length_35(self):
        return _format_focal_length(self.exif.focal_length_35)

    @property
    def exposure(self):
        parts = []
        if self.shutter:
            parts.append(self.shutter)
        if self.aperture:
            parts.append(self.aperture)
        if self.iso:
            parts.append(f"ISO{self.iso}")
        if self.focal_length_35:
            parts.append(self.focal_length_35)
        return " ".join(parts) if parts else None

    @property
    def sublocation(self):
        return self.iptc.sublocation

    @property
    def city(self):
        return self.iptc.city

    @property
    def province_state(self):
        return self.iptc.province_state

    @property
    def state(self):
        return self.iptc.province_state

    @property
    def province(self):
        return self.iptc.province_state

    @property
    def country(self):
        return self.iptc.country

    @property
    def country_code(self):
        return self.iptc.country_code

    @property
    def location(self):
        parts = [
            p
            for p in (
                self.sublocation,
                self.city,
                self.province_state,
                self.country,
            )
            if p
        ]
        return ", ".join(parts) if parts else None

    @property
    def latitude(self):
        return _parse_gps_coordinate(self.exif.latitude, self.exif.latitude_ref)

    @property
    def longitude(self):
        return _parse_gps_coordinate(self.exif.longitude, self.exif.longitude_ref)

    @property
    def keywords(self):
        return self.iptc.keywords or self.xmp.subject or []

    @property
    def rating(self):
        r = self.xmp.rating
        if r is None:
            return 0
        try:
            return int(r)
        except ValueError, TypeError:
            return 0


def read_metadata(path):
    """Read EXIF, IPTC, and XMP metadata from an image file.

    Returns a Metadata object with raw layers and derived properties.
    """
    file_layer = _build_file_layer(path)

    try:
        img = pyexiv2.Image(str(path))
        try:
            exif = img.read_exif()
            iptc = img.read_iptc()
            xmp = img.read_xmp()
            try:
                file_layer.width = img.get_pixel_width()
                file_layer.height = img.get_pixel_height()
            except Exception:
                pass
        finally:
            img.close()
    except Exception:
        logger.debug("Failed to read metadata from %s", path, exc_info=True)
        return Metadata(file=file_layer)

    exif_layer = _build_exif_layer(exif)
    iptc_layer = _build_iptc_layer(iptc)
    xmp_layer = _build_xmp_layer(xmp)

    return Metadata(file=file_layer, exif=exif_layer, iptc=iptc_layer, xmp=xmp_layer)


_COPYRIGHT_KEYS = {
    "exif": ("Exif.Image.Artist", "Exif.Image.Copyright"),
    "iptc": ("Iptc.Application2.Byline", "Iptc.Application2.Copyright"),
    "xmp": ("Xmp.dc.creator", "Xmp.dc.rights"),
}


def strip_metadata(path):
    """Strip metadata from an image file in-place, preserving copyright info."""
    try:
        img = pyexiv2.Image(str(path))
        try:
            exif = img.read_exif()
            iptc = img.read_iptc()
            xmp = img.read_xmp()

            keep_exif = {k: exif[k] for k in _COPYRIGHT_KEYS["exif"] if k in exif}
            keep_iptc = {k: iptc[k] for k in _COPYRIGHT_KEYS["iptc"] if k in iptc}
            keep_xmp = {k: xmp[k] for k in _COPYRIGHT_KEYS["xmp"] if k in xmp}

            img.clear_exif()
            img.clear_iptc()
            img.clear_xmp()

            if keep_exif:
                img.modify_exif(keep_exif)
            if keep_iptc:
                img.modify_iptc(keep_iptc)
            if keep_xmp:
                img.modify_xmp(keep_xmp)
        finally:
            img.close()
    except Exception:
        logger.debug("Failed to strip metadata from %s", path, exc_info=True)
