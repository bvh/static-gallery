import pytest

from tests.helpers import make_node
from static_gallery.index import SuffixIndex
from static_gallery.node import NodeType


def test_resolve_unique_filename():
    index = SuffixIndex("/src")
    node = make_node("/src/photos/cat.jpg", NodeType.IMAGE, suffix=".jpg")
    index.add(node)
    assert index.resolve("cat.jpg") is node


def test_resolve_unique_suffix():
    index = SuffixIndex("/src")
    node = make_node("/src/photos/belfast/photo1.jpg", NodeType.IMAGE, suffix=".jpg")
    index.add(node)
    assert index.resolve("belfast/photo1.jpg") is node


def test_resolve_ambiguous_raises():
    index = SuffixIndex("/src")
    node1 = make_node("/src/photos/photo1.jpg", NodeType.IMAGE, suffix=".jpg")
    node2 = make_node("/src/travel/photo1.jpg", NodeType.IMAGE, suffix=".jpg")
    index.add(node1)
    index.add(node2)
    with pytest.raises(ValueError, match="Ambiguous shortcode path"):
        index.resolve("photo1.jpg")


def test_resolve_not_found_raises():
    index = SuffixIndex("/src")
    with pytest.raises(ValueError, match="Shortcode target not found"):
        index.resolve("nonexistent.jpg")


def test_resolve_absolute_exact():
    index = SuffixIndex("/src")
    node = make_node("/src/photos/cat.jpg", NodeType.IMAGE, suffix=".jpg")
    index.add(node)
    assert index.resolve("/photos/cat.jpg") is node


def test_resolve_absolute_not_found_raises():
    index = SuffixIndex("/src")
    with pytest.raises(ValueError, match="Shortcode target not found"):
        index.resolve("/missing.jpg")


def test_resolve_full_relative_path():
    index = SuffixIndex("/src")
    node = make_node("/src/photos/cat.jpg", NodeType.IMAGE, suffix=".jpg")
    index.add(node)
    assert index.resolve("photos/cat.jpg") is node
