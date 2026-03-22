import os

from static_gallery.metadata import Metadata
from static_gallery.node import Node


def make_metadata(**kwargs):
    """Create a Metadata object, optionally overriding derived property values.

    For testing convenience, this creates a Metadata with empty layers,
    then patches the raw layers so derived properties return the given values.
    Supported kwargs map to derived property names.
    """
    m = Metadata()
    # Map derived property kwargs to the appropriate raw layer fields
    field_map = {
        "title": ("iptc", "name"),
        "description": ("exif", "description"),
        "alt_text": ("xmp", "alt_text"),
        "artist": ("exif", "artist"),
        "copyright": ("exif", "copyright"),
        "camera": ("exif", "camera"),
        "camera_make": ("exif", "camera_make"),
        "lens": ("exif", "lens"),
        "lens_info": ("exif", "lens_info"),
        "lens_make": ("exif", "lens_make"),
        "shutter": ("exif", "shutter_speed"),
        "aperture": ("exif", "aperture"),
        "iso": ("exif", "iso"),
        "focal_length": ("exif", "focal_length"),
        "focal_length_35": ("exif", "focal_length_35"),
        "sublocation": ("iptc", "sublocation"),
        "city": ("iptc", "city"),
        "province_state": ("iptc", "province_state"),
        "country": ("iptc", "country"),
        "country_code": ("iptc", "country_code"),
        "keywords": ("iptc", "keywords"),
        "rating": ("xmp", "rating"),
    }
    for key, value in kwargs.items():
        if key == "datetime":
            # Store as raw EXIF datetime string if it's a string,
            # otherwise store in iptc.date for the fallback
            setattr(m.exif, "datetime", value)
        elif key in field_map:
            layer_name, field_name = field_map[key]
            layer = getattr(m, layer_name)
            setattr(layer, field_name, value)
    return m


def make_node(path, type, name=None, stem=None, suffix="", metadata=None):
    node = Node.__new__(Node)
    node.path = path
    node.type = type
    node.name = name or os.path.basename(path)
    node.stem = stem or os.path.splitext(node.name)[0]
    node.suffix = suffix
    node._metadata = metadata if metadata is not None else None
    node.images = []
    node.pages = []
    node.assets = []
    node.dirs = []
    node.index_path = None
    node.content_path = None
    return node
