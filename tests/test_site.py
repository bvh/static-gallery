from tests.helpers import make_node
from static_gallery.index import SuffixIndex
from static_gallery.node import NodeType
from static_gallery.site import Site


def test_site_stores_root_and_source_path():
    root = make_node("/src", NodeType.HOME)
    site = Site(root, "/src")
    assert site.root is root
    assert site.source_path == "/src"


def test_site_stores_explicit_index():
    root = make_node("/src", NodeType.HOME)
    index = SuffixIndex("/src")
    site = Site(root, "/src", index)
    assert site.index is index


def test_site_builds_index_lazily():
    root = make_node("/src", NodeType.HOME)
    child = make_node("/src/photo.jpg", NodeType.IMAGE, suffix=".jpg")
    root.add_child(child)

    site = Site(root, "/src")
    resolved = site.index.resolve("photo.jpg")
    assert resolved is child


def test_site_lazy_index_built_once():
    root = make_node("/src", NodeType.HOME)
    site = Site(root, "/src")
    first = site.index
    second = site.index
    assert first is second
