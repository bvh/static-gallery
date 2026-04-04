import os
from datetime import datetime

import pyexiv2
import pytest

from static_gallery.metadata import Metadata, read_metadata, strip_metadata

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


# --- Metadata class returns ---


def test_read_metadata_returns_metadata(fixture_image):
    meta = read_metadata(fixture_image)
    assert isinstance(meta, Metadata)


# --- Raw layers exist ---


def test_raw_layers_exist(fixture_image):
    meta = read_metadata(fixture_image)
    assert hasattr(meta, "file")
    assert hasattr(meta, "exif")
    assert hasattr(meta, "iptc")
    assert hasattr(meta, "xmp")


# --- Raw EXIF layer ---


def test_raw_exif_camera(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.camera == "EOS R5"
    assert meta.exif.camera_make == "Canon"


def test_raw_exif_description(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.description == "A beautiful sunset"


def test_raw_exif_artist(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.artist == "Jane Doe"


def test_raw_exif_datetime(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.datetime == "2024:06:15 18:30:00"


def test_raw_exif_exposure(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.shutter_speed == "1/250"
    assert meta.exif.aperture == "28/10"
    assert meta.exif.iso == "400"
    assert meta.exif.focal_length == "50/1"
    assert meta.exif.focal_length_35 == "75"


def test_raw_exif_lens(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.lens == "RF 50mm F1.2L USM"
    assert meta.exif.lens_make == "Canon"


def test_raw_exif_gps(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exif.latitude == "48/1 51/1 24/1"
    assert meta.exif.latitude_ref == "N"
    assert meta.exif.longitude == "2/1 21/1 3/1"
    assert meta.exif.longitude_ref == "E"


# --- Raw IPTC layer ---


def test_raw_iptc_name(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.iptc.name == "Sunset Photo"


def test_raw_iptc_location(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.iptc.country_code == "FR"
    assert meta.iptc.country == "France"
    assert meta.iptc.province_state == "Île-de-France"
    assert meta.iptc.city == "Paris"
    assert meta.iptc.sublocation == "Eiffel Tower"


def test_raw_iptc_keywords(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.iptc.keywords == ["sunset", "landscape", "nature"]


# --- Raw XMP layer ---


def test_raw_xmp_rating(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.xmp.rating == "5"


# --- Raw file layer ---


def test_raw_file_name(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.file.name == "photo"


def test_raw_file_type(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.file.type == "image/jpeg"


def test_raw_file_timestamps(fixture_image):
    meta = read_metadata(fixture_image)
    stat = os.stat(fixture_image)
    assert meta.file.mtime == stat.st_mtime
    assert meta.file.ctime == stat.st_ctime


def test_raw_file_dimensions(fixture_image):
    meta = read_metadata(fixture_image)
    # Minimal JPEG may have 0 or 1 pixel dimensions
    assert isinstance(meta.file.width, int)
    assert isinstance(meta.file.height, int)


# --- Derived properties: basic fields ---


def test_derived_title(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.title == "Sunset Photo"


def test_derived_description(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.description == "A beautiful sunset"


def test_derived_artist(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.artist == "Jane Doe"


def test_derived_copyright(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.copyright == "2024 Jane Doe"


def test_derived_camera(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.camera == "EOS R5"


def test_derived_datetime(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.datetime == datetime(2024, 6, 15, 18, 30, 0)


def test_derived_exposure_fields(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.shutter == "1/250"
    assert meta.aperture == "f/2.8"
    assert meta.iso == "400"
    assert meta.focal_length == "50mm"
    assert meta.focal_length_35 == "75mm"


def test_derived_exposure_string(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.exposure == "1/250 f/2.8 ISO400 75mm"


def test_derived_lens(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.lens == "RF 50mm F1.2L USM"
    assert meta.lens_make == "Canon"


def test_derived_gps(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.latitude == pytest.approx(48.856667, abs=0.001)
    assert meta.longitude == pytest.approx(2.350833, abs=0.001)


def test_derived_location_fields(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.sublocation == "Eiffel Tower"
    assert meta.city == "Paris"
    assert meta.province_state == "Île-de-France"
    assert meta.state == "Île-de-France"
    assert meta.province == "Île-de-France"
    assert meta.country == "France"


def test_derived_location_composite(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.location == "Eiffel Tower, Paris, Île-de-France, France"


def test_derived_keywords(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.keywords == ["sunset", "landscape", "nature"]


def test_derived_rating(fixture_image):
    meta = read_metadata(fixture_image)
    assert meta.rating == 5


# --- Bare image: defaults and fallbacks ---


def test_bare_title_falls_back_to_filename(bare_image):
    meta = read_metadata(bare_image)
    assert meta.title == "bare"


def test_bare_description_is_none(bare_image):
    meta = read_metadata(bare_image)
    assert meta.description is None


def test_bare_alt_text_falls_back_to_title(bare_image):
    meta = read_metadata(bare_image)
    assert meta.alt_text == "bare"


def test_bare_datetime_falls_back_to_ctime(bare_image):
    meta = read_metadata(bare_image)
    assert isinstance(meta.datetime, datetime)
    stat = os.stat(bare_image)
    assert meta.datetime == datetime.fromtimestamp(stat.st_ctime)


def test_bare_camera_is_none(bare_image):
    meta = read_metadata(bare_image)
    assert meta.camera is None


def test_bare_keywords_default_empty_list(bare_image):
    meta = read_metadata(bare_image)
    assert meta.keywords == []


def test_bare_rating_default_zero(bare_image):
    meta = read_metadata(bare_image)
    assert meta.rating == 0


def test_bare_location_is_none(bare_image):
    meta = read_metadata(bare_image)
    assert meta.location is None


def test_bare_exposure_is_none(bare_image):
    meta = read_metadata(bare_image)
    assert meta.exposure is None


def test_bare_latitude_is_none(bare_image):
    meta = read_metadata(bare_image)
    assert meta.latitude is None


# --- Fallback chains ---


def test_alt_text_falls_back_to_description(fixture_image):
    """alt_text should fall back to description when XMP alt text is absent."""
    meta = read_metadata(fixture_image)
    assert meta.alt_text == "A beautiful sunset"


def test_alt_text_falls_back_to_title(tmp_path):
    """alt_text falls back to title when description is also absent."""
    path = _make_jpeg(tmp_path, "titled.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc({"Iptc.Application2.ObjectName": "My Title Only"})
    img.close()
    meta = read_metadata(path)
    assert meta.alt_text == "My Title Only"


def test_description_iptc_fallback(tmp_path):
    """description falls back to IPTC caption."""
    path = _make_jpeg(tmp_path, "captioned.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc({"Iptc.Application2.Caption": "IPTC caption text"})
    img.close()
    meta = read_metadata(path)
    assert meta.description == "IPTC caption text"


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
    assert meta.datetime == datetime(2024, 6, 15, 18, 30, 0)


def test_keywords_xmp_fallback(tmp_path):
    """keywords falls back to XMP subject when IPTC keywords are absent."""
    path = _make_jpeg(tmp_path, "xmp_kw.jpg")
    img = pyexiv2.Image(path)
    img.modify_xmp({"Xmp.dc.subject": ["travel", "urban"]})
    img.close()
    meta = read_metadata(path)
    assert meta.keywords == ["travel", "urban"]


# --- Shutter speed formatting ---


def test_shutter_speed_long_exposure_integer(tmp_path):
    """Shutter speed >= 1s with integer value like '30/1' → '30s'."""
    path = _make_jpeg(tmp_path, "long_exp.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif({"Exif.Photo.ExposureTime": "30/1"})
    img.close()
    meta = read_metadata(path)
    assert meta.shutter == "30s"


def test_shutter_speed_long_exposure_fractional(tmp_path):
    """Shutter speed >= 1s with fractional value like '15/10' → '1.5s'."""
    path = _make_jpeg(tmp_path, "frac_exp.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif({"Exif.Photo.ExposureTime": "15/10"})
    img.close()
    meta = read_metadata(path)
    assert meta.shutter == "1.5s"


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
    assert meta.latitude < 0
    assert meta.longitude < 0


# --- Location composite partial ---


def test_location_partial(tmp_path):
    """Location composite should join only non-None parts."""
    path = _make_jpeg(tmp_path, "partial_loc.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc(
        {
            "Iptc.Application2.City": "Tokyo",
            "Iptc.Application2.CountryName": "Japan",
        }
    )
    img.close()
    meta = read_metadata(path)
    assert meta.location == "Tokyo, Japan"


# --- Exposure partial ---


def test_exposure_partial(tmp_path):
    """Exposure string with only some components present."""
    path = _make_jpeg(tmp_path, "partial_exp.jpg")
    img = pyexiv2.Image(path)
    img.modify_exif(
        {
            "Exif.Photo.ExposureTime": "1/125",
            "Exif.Photo.FNumber": "4/1",
        }
    )
    img.close()
    meta = read_metadata(path)
    assert meta.exposure == "1/125 f/4"


# --- Error handling ---


def test_read_metadata_nonexistent_file(tmp_path):
    """read_metadata on a nonexistent file returns Metadata with None raw fields."""
    meta = read_metadata(str(tmp_path / "nonexistent.jpg"))
    assert isinstance(meta, Metadata)
    assert meta.title == "nonexistent"
    assert meta.camera is None


# --- strip_metadata ---


def test_strip_metadata_removes_non_copyright_exif(fixture_image):
    """strip_metadata removes GPS, camera, etc. but keeps artist and copyright."""
    strip_metadata(fixture_image)
    img = pyexiv2.Image(fixture_image)
    exif = img.read_exif()
    img.close()
    assert "Exif.Image.Artist" in exif
    assert exif["Exif.Image.Artist"] == "Jane Doe"
    assert "Exif.Image.Copyright" in exif
    assert exif["Exif.Image.Copyright"] == "2024 Jane Doe"
    assert "Exif.GPSInfo.GPSLatitude" not in exif
    assert "Exif.Image.Model" not in exif
    assert "Exif.Photo.FocalLength" not in exif


def test_strip_metadata_preserves_iptc_copyright(tmp_path):
    """strip_metadata keeps IPTC byline and copyright, removes other IPTC fields."""
    path = _make_jpeg(tmp_path, "iptc_test.jpg")
    img = pyexiv2.Image(path)
    img.modify_iptc(
        {
            "Iptc.Application2.Byline": "John Smith",
            "Iptc.Application2.Copyright": "2024 John Smith",
            "Iptc.Application2.City": "Paris",
            "Iptc.Application2.Keywords": ["test"],
        }
    )
    img.close()

    strip_metadata(path)

    img = pyexiv2.Image(path)
    iptc = img.read_iptc()
    img.close()
    assert iptc.get("Iptc.Application2.Byline") == ["John Smith"]
    assert iptc.get("Iptc.Application2.Copyright") == "2024 John Smith"
    assert "Iptc.Application2.City" not in iptc
    assert "Iptc.Application2.Keywords" not in iptc


def test_strip_metadata_preserves_xmp_copyright(tmp_path):
    """strip_metadata keeps XMP creator and rights, removes other XMP fields."""
    path = _make_jpeg(tmp_path, "xmp_test.jpg")
    img = pyexiv2.Image(path)
    img.modify_xmp(
        {
            "Xmp.dc.creator": ["Jane Doe"],
            "Xmp.dc.rights": "2024 Jane Doe",
            "Xmp.xmp.Rating": "5",
        }
    )
    img.close()

    strip_metadata(path)

    img = pyexiv2.Image(path)
    xmp = img.read_xmp()
    img.close()
    assert "Xmp.dc.creator" in xmp
    assert "Xmp.dc.rights" in xmp
    assert "Xmp.xmp.Rating" not in xmp


def test_strip_metadata_preserves_image_data(fixture_image):
    """Stripped JPEG is still a valid JPEG."""
    original_size = os.path.getsize(fixture_image)
    strip_metadata(fixture_image)
    with open(fixture_image, "rb") as f:
        header = f.read(2)
    assert header == b"\xff\xd8"  # JPEG magic bytes
    assert os.path.getsize(fixture_image) < original_size


def test_strip_metadata_handles_unsupported_format(tmp_path):
    """strip_metadata silently skips files pyexiv2 cannot handle."""
    path = tmp_path / "fake.gif"
    path.write_bytes(b"GIF89a" + b"\x00" * 100)
    original = path.read_bytes()
    strip_metadata(str(path))
    assert path.read_bytes() == original


def test_strip_metadata_nonexistent_file(tmp_path):
    """strip_metadata does not raise on a missing file."""
    strip_metadata(str(tmp_path / "missing.jpg"))
