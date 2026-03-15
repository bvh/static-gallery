import logging
import os
from unittest.mock import patch

import pytest

from static_gallery.node import Node, NodeType


class TestInit:
    def test_init_with_path_string(self, tmp_path):
        d = tmp_path / "mydir"
        d.mkdir()
        node = Node(str(d))
        assert node.path == str(d)
        assert node.name == "mydir"
        assert node.stem == "mydir"
        assert node.suffix == ""
        assert node.is_dir()

    def test_init_with_file_path(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f))
        assert node.name == "photo.jpg"
        assert node.stem == "photo"
        assert node.suffix == ".jpg"
        assert not node.is_dir()

    def test_init_with_direntry(self, tmp_path):
        (tmp_path / "entry.md").write_text("# Hi")
        with os.scandir(tmp_path) as it:
            for entry in it:
                if entry.name == "entry.md":
                    node = Node(entry)
                    break
        assert node.path == str(tmp_path / "entry.md")
        assert node.name == "entry.md"
        assert node.stem == "entry"
        assert node.suffix == ".md"

    def test_init_defaults(self, tmp_path):
        node = Node(str(tmp_path))
        assert node.type is None
        assert node.parent is None
        assert node.index_path is None
        assert node.content_path is None
        assert node.dirs == []
        assert node.pages == []
        assert node.images == []
        assert node.assets == []


class TestClassification:
    def test_is_image(self, tmp_path):
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            f = tmp_path / f"img{ext}"
            f.write_bytes(b"\x00")
            assert Node(str(f)).is_image()

    def test_is_not_image(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("hello")
        assert not Node(str(f)).is_image()

    def test_is_markdown(self, tmp_path):
        for ext in [".md", ".markdown"]:
            f = tmp_path / f"doc{ext}"
            f.write_text("# Hi")
            assert Node(str(f)).is_markdown()

    def test_is_not_markdown(self, tmp_path):
        f = tmp_path / "style.css"
        f.write_text("body {}")
        assert not Node(str(f)).is_markdown()

    def test_is_dir(self, tmp_path):
        d = tmp_path / "sub"
        d.mkdir()
        assert Node(str(d)).is_dir()

    def test_is_not_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hi")
        assert not Node(str(f)).is_dir()


class TestAddChild:
    def _make_child(self, tmp_path, name, node_type):
        p = tmp_path / name
        if node_type in (NodeType.DIRECTORY, NodeType.GALLERY):
            p.mkdir()
        else:
            p.write_bytes(b"\x00")
        return Node(str(p), type=node_type)

    def test_add_markdown(self, tmp_path):
        parent = Node(str(tmp_path))
        child = self._make_child(tmp_path, "x.md", NodeType.MARKDOWN)
        parent.add_child(child)
        assert child in parent.pages

    def test_add_image(self, tmp_path):
        parent = Node(str(tmp_path))
        child = self._make_child(tmp_path, "x.jpg", NodeType.IMAGE)
        parent.add_child(child)
        assert child in parent.images

    def test_add_static(self, tmp_path):
        parent = Node(str(tmp_path))
        child = self._make_child(tmp_path, "x.css", NodeType.STATIC)
        parent.add_child(child)
        assert child in parent.assets

    def test_add_directory(self, tmp_path):
        parent = Node(str(tmp_path))
        child = self._make_child(tmp_path, "sub", NodeType.DIRECTORY)
        parent.add_child(child)
        assert child in parent.dirs

    def test_add_gallery(self, tmp_path):
        parent = Node(str(tmp_path))
        child = self._make_child(tmp_path, "photos", NodeType.GALLERY)
        parent.add_child(child)
        assert child in parent.dirs

    def test_add_unknown_type_raises(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_bytes(b"\x00")
        parent = Node(str(tmp_path))
        child = Node(str(f))
        child.type = "BOGUS"
        with pytest.raises(ValueError, match="Unknown node type"):
            parent.add_child(child)


class TestTemplateName:
    def test_gallery(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.GALLERY)
        assert node.template_name == "gallery.html"

    def test_directory_without_index(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.DIRECTORY)
        assert node.template_name == "directory.html"

    def test_directory_with_index(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.DIRECTORY)
        node.index_path = "/some/index.md"
        assert node.template_name == "default.html"

    def test_home(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.HOME)
        assert node.template_name == "default.html"

    def test_markdown(self, tmp_path):
        f = tmp_path / "page.md"
        f.write_text("# Hi")
        node = Node(str(f), type=NodeType.MARKDOWN)
        assert node.template_name == "default.html"

    def test_image(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        assert node.template_name == "image.html"


class TestTitleFallback:
    def test_markdown_uses_stem(self, tmp_path):
        f = tmp_path / "my-page.md"
        f.write_text("# Hi")
        node = Node(str(f), type=NodeType.MARKDOWN)
        assert node.title_fallback == "my-page"

    def test_image_uses_stem(self, tmp_path):
        f = tmp_path / "sunset.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        assert node.title_fallback == "sunset"

    def test_other_uses_name(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.DIRECTORY)
        assert node.title_fallback == node.name


class TestIsGallery:
    def test_images_only(self, tmp_path):
        node = Node(str(tmp_path))
        img = tmp_path / "x.jpg"
        img.write_bytes(b"\x00")
        node.images = [Node(str(img), type=NodeType.IMAGE)]
        assert node.is_gallery()

    def test_images_and_pages(self, tmp_path):
        node = Node(str(tmp_path))
        img = tmp_path / "x.jpg"
        img.write_bytes(b"\x00")
        page = tmp_path / "y.md"
        page.write_text("# Hi")
        node.images = [Node(str(img), type=NodeType.IMAGE)]
        node.pages = [Node(str(page), type=NodeType.MARKDOWN)]
        assert not node.is_gallery()

    def test_empty(self, tmp_path):
        node = Node(str(tmp_path))
        assert not node.is_gallery()


class TestGetMarkdownPath:
    def test_markdown_returns_own_path(self, tmp_path):
        f = tmp_path / "page.md"
        f.write_text("# Hi")
        node = Node(str(f), type=NodeType.MARKDOWN)
        assert node.get_markdown_path() == str(f)

    def test_container_returns_index_path(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.HOME)
        node.index_path = "/some/index.md"
        assert node.get_markdown_path() == "/some/index.md"

    def test_container_returns_none_without_index(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.DIRECTORY)
        assert node.get_markdown_path() is None

    def test_image_returns_content_path(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        node.content_path = "/some/photo.md"
        assert node.get_markdown_path() == "/some/photo.md"

    def test_image_returns_none_without_content_path(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        assert node.get_markdown_path() is None


class TestMetadata:
    def test_non_image_returns_empty(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.DIRECTORY)
        assert node.metadata == {}

    def test_lazy_loading(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        with patch("static_gallery.node.read_metadata", return_value={"title": "T"}):
            result = node.metadata
            assert result == {"title": "T"}
            # Second access uses cached value
            result2 = node.metadata
            assert result2 is result

    def test_error_logs_warning(self, tmp_path, caplog):
        f = tmp_path / "bad.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        with (
            patch(
                "static_gallery.node.read_metadata", side_effect=RuntimeError("boom")
            ),
            caplog.at_level(logging.WARNING, logger="static_gallery.node"),
        ):
            result = node.metadata
        assert result == {}
        assert "Failed to read metadata" in caplog.text


class TestToDict:
    def test_basic_shape(self, tmp_path):
        f = tmp_path / "page.md"
        f.write_text("# Hi")
        node = Node(str(f), type=NodeType.MARKDOWN)
        d = node.to_dict()
        assert d["type"] == "MARKDOWN"
        assert d["path"] == str(f)
        assert d["stem"] == "page"
        assert d["suffix"] == ".md"
        assert "mtime" in d

    def test_children_included(self, tmp_path):
        parent = Node(str(tmp_path), type=NodeType.HOME)
        child = Node(str(tmp_path), type=NodeType.MARKDOWN)
        parent.add_child(child)
        d = parent.to_dict()
        assert "pages" in d
        assert len(d["pages"]) == 1

    def test_parent_path_included(self, tmp_path):
        parent = Node(str(tmp_path), type=NodeType.HOME)
        f = tmp_path / "page.md"
        f.write_text("# Hi")
        child = Node(str(f), parent=parent, type=NodeType.MARKDOWN)
        d = child.to_dict()
        assert d["parent"] == str(tmp_path)

    def test_content_path_included(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        node.content_path = "/some/photo.md"
        d = node.to_dict()
        assert d["content_path"] == "/some/photo.md"

    def test_content_path_omitted_when_none(self, tmp_path):
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\x00")
        node = Node(str(f), type=NodeType.IMAGE)
        d = node.to_dict()
        assert "content_path" not in d

    def test_empty_children_omitted(self, tmp_path):
        node = Node(str(tmp_path), type=NodeType.HOME)
        d = node.to_dict()
        assert "pages" not in d
        assert "images" not in d
        assert "assets" not in d
        assert "dirs" not in d
