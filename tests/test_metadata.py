from datetime import datetime

import pyexiv2
import pytest

from static_gallery.metadata import read_metadata
from static_gallery.node import Node

# Minimal valid JPEG (SOI + APP0 + EOI)
MINIMAL_JPEG = bytes(
    [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00]
    + [0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00]
    + [0xFF, 0xD9]
)


def _make_jpeg(tmp_path, name="photo.jpg"):
    """Write a minimal JPEG to tmp_path and return its string path."""
    path = str(tmp_path / name)
    with open(path, "wb") as f:
        f.write(MINIMAL_JPEG)
    return path


@pytest.fixture()
def fixture_image(tmp_path):
    """Create a minimal JPEG with rich EXIF/IPTC/XMP metadata using pyexiv2."""
    path = _make_jpeg(tmp_path)

    img = pyexiv2.Image(path)
    img.modify_exif(
        {
            "Exif.Image.ImageDescription": "A beautiful sunset",
            "Exif.Image.Artist": "Jane Doe",
            "Exif.Image.Copyright": "2024 Jane Doe",
            "Exif.Image.Make": "Canon",
            "Exif.Image.Model": "EOS R5",
            "Exif.Photo.DateTimeOriginal": "2024:06:15 18:30:00",
            "Exif.Photo.ExposureTime": "1/250",
            "Exif.Photo.FNumber": "28/10",
            "Exif.Photo.ISOSpeedRatings": "400",
            "Exif.Photo.FocalLength": "50/1",
            "Exif.Photo.FocalLengthIn35mmFilm": "75",
            "Exif.Photo.LensModel": "RF 50mm F1.2L USM",
            "Exif.Photo.LensMake": "Canon",
            "Exif.GPSInfo.GPSLatitude": "48/1 51/1 24/1",
            "Exif.GPSInfo.GPSLatitudeRef": "N",
            "Exif.GPSInfo.GPSLongitude": "2/1 21/1 3/1",
            "Exif.GPSInfo.GPSLongitudeRef": "E",
        }
    )
    img.modify_iptc(
        {
            "Iptc.Application2.ObjectName": "Sunset Photo",
            "Iptc.Application2.Keywords": ["sunset", "landscape", "nature"],
            "Iptc.Application2.CountryCode": "FR",
            "Iptc.Application2.CountryName": "France",
            "Iptc.Application2.ProvinceState": "Île-de-France",
            "Iptc.Application2.City": "Paris",
            "Iptc.Application2.SubLocation": "Eiffel Tower",
        }
    )
    img.modify_xmp(
        {
            "Xmp.xmp.Rating": "5",
        }
    )
    img.close()
    return path


@pytest.fixture()
def bare_image(tmp_path):
    """Create a minimal JPEG with no metadata."""
    return _make_jpeg(tmp_path, "bare.jpg")


# --- read_metadata basic fields ---


def test_read_metadata_title(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["title"] == "Sunset Photo"


def test_read_metadata_description(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["description"] == "A beautiful sunset"


def test_read_metadata_artist(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["artist"] == "Jane Doe"


def test_read_metadata_copyright(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["copyright"] == "2024 Jane Doe"


def test_read_metadata_camera(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["camera"] == "EOS R5"
    assert meta["camera_make"] == "Canon"


def test_read_metadata_datetime(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["datetime"] == datetime(2024, 6, 15, 18, 30, 0)


def test_read_metadata_exposure(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["shutter"] == "1/250"
    assert meta["aperture"] == "f/2.8"
    assert meta["iso"] == "400"


def test_read_metadata_focal_length(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["focal_length"] == "50mm"
    assert meta["focal_length_35"] == "75mm"


def test_read_metadata_lens(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["lens_model"] == "RF 50mm F1.2L USM"
    assert meta["lens_make"] == "Canon"


def test_read_metadata_gps(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["gps_latitude"] == pytest.approx(48.856667, abs=0.001)
    assert meta["gps_longitude"] == pytest.approx(2.350833, abs=0.001)


def test_read_metadata_location(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["country_code"] == "FR"
    assert meta["country"] == "France"
    assert meta["province_state"] == "Île-de-France"
    assert meta["city"] == "Paris"
    assert meta["location"] == "Eiffel Tower"


def test_read_metadata_keywords(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["keywords"] == ["sunset", "landscape", "nature"]


def test_read_metadata_rating(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["rating"] == "5"


def test_read_metadata_aliases(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta["state"] == meta["province_state"]
    assert meta["province"] == meta["province_state"]


# --- bare image returns Nones ---


def test_read_metadata_bare_image(bare_image):
    meta = read_metadata(bare_image)
    assert meta["title"] is None
    assert meta["description"] is None
    assert meta["camera"] is None
    assert meta["datetime"] is None
    assert meta["gps_latitude"] is None
    assert meta["keywords"] is None


# --- fallback chains ---


def test_alt_text_falls_back_to_description(fixture_image):
    """alt_text should fall back to description when Xmp.iptcExt.AltTextAccessibility is absent."""
    meta = read_metadata(fixture_image)
    assert meta["alt_text"] == "A beautiful sunset"


def test_alt_text_falls_back_to_title(tmp_path):
    """alt_text falls back to title when description is also absent."""
    path = _make_jpeg(tmp_path, "titled.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc({"Iptc.Application2.ObjectName": "My Title Only"})
    img.close()
    meta = read_metadata(path)
    assert meta["alt_text"] == "My Title Only"


def test_description_iptc_fallback(tmp_path):
    """description falls back to Iptc.Application2.Caption."""
    path = _make_jpeg(tmp_path, "captioned.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc({"Iptc.Application2.Caption": "IPTC caption text"})
    img.close()
    meta = read_metadata(path)
    assert meta["description"] == "IPTC caption text"


def test_datetime_iptc_fallback(tmp_path):
    """datetime falls back to IPTC DateCreated + TimeCreated."""
    path = _make_jpeg(tmp_path, "iptcdate.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc(
        {
            "Iptc.Application2.DateCreated": "2024-06-15",
            "Iptc.Application2.TimeCreated": "18:30:00+00:00",
        }
    )
    img.close()
    meta = read_metadata(path)
    assert meta["datetime"] == datetime(2024, 6, 15, 18, 30, 0)


# --- shutter speed formatting ---


def test_shutter_speed_long_exposure_integer(tmp_path):
    """Shutter speed >= 1s with integer value like '30/1' → '30s'."""
    path = _make_jpeg(tmp_path, "long_exp.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif({"Exif.Photo.ExposureTime": "30/1"})
    img.close()
    meta = read_metadata(path)
    assert meta["shutter"] == "30s"


def test_shutter_speed_long_exposure_fractional(tmp_path):
    """Shutter speed >= 1s with fractional value like '15/10' → '1.5s'."""
    path = _make_jpeg(tmp_path, "frac_exp.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif({"Exif.Photo.ExposureTime": "15/10"})
    img.close()
    meta = read_metadata(path)
    assert meta["shutter"] == "1.5s"


# --- XMP keywords fallback ---


def test_keywords_xmp_fallback(tmp_path):
    """keywords falls back to Xmp.dc.subject when IPTC keywords are absent."""
    path = _make_jpeg(tmp_path, "xmp_kw.jpg")
    img = pyexiv2.Image(path)
    img.modify_xmp({"Xmp.dc.subject": ["travel", "urban"]})
    img.close()
    meta = read_metadata(path)
    assert meta["keywords"] == ["travel", "urban"]


# --- GPS sign for S/W ---


def test_gps_south_west(tmp_path):
    """GPS coordinates should be negative for S and W references."""
    path = _make_jpeg(tmp_path, "south.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif(
        {
            "Exif.GPSInfo.GPSLatitude": "33/1 52/1 10/1",
            "Exif.GPSInfo.GPSLatitudeRef": "S",
            "Exif.GPSInfo.GPSLongitude": "151/1 12/1 30/1",
            "Exif.GPSInfo.GPSLongitudeRef": "W",
        }
    )
    img.close()
    meta = read_metadata(path)
    assert meta["gps_latitude"] < 0
    assert meta["gps_longitude"] < 0


# --- Node.metadata lazy property ---


def test_node_metadata_lazy(fixture_image):
    """IMAGE node should lazily load metadata on first access."""
    node = Node(fixture_image, type="IMAGE")
    # _metadata sentinel should not exist yet
    assert not hasattr(node, "_metadata") or node._metadata is None
    meta = node.metadata
    assert meta["title"] == "Sunset Photo"
    # Second access returns same dict (cached)
    assert node.metadata is meta


def test_node_metadata_non_image(tmp_path):
    """Non-IMAGE nodes return empty dict."""
    sub = tmp_path / "dir"
    sub.mkdir()
    node = Node(str(sub), type="DIRECTORY")
    assert node.metadata == {}


def test_node_metadata_error_returns_nones(tmp_path):
    """If metadata reading fails, return dict with all None values."""
    path = tmp_path / "nonexistent.jpg"
    node = Node.__new__(Node)
    node.type = "IMAGE"
    node.path = str(path)
    node._metadata = None
    meta = node.metadata
    assert meta["title"] is None
    assert meta["camera"] is None
    assert meta["keywords"] is None
