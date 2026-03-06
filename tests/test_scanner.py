import pytest
from pathlib import Path
from static_gallery.scanner import scan
from static_gallery.model import Node, NodeType


def _make_file(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _all_source_nodes(node):
    """Collect all nodes that have a source file (including collapsed index dirs)."""
    result = []
    if node.source is not None:
        result.append(node)
    for child in node.children:
        result.extend(_all_source_nodes(child))
    return result


def _find_child(node, name):
    return next(c for c in node.children if c.name == name)


class TestScan:
    def test_markdown_classified(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, "site.conf")
        # index.md collapses into root
        assert tree.node_type == NodeType.MARKDOWN
        assert tree.source == source / "index.md"

    def test_image_classified(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "photo.jpg", "fake image")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1
        assert files[0].node_type == NodeType.IMAGE
        assert files[0].source == source / "photo.jpg"

    def test_static_classified(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "styles.css", "body {}")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1
        assert files[0].node_type == NodeType.STATIC

    def test_dotfile_excluded(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / ".hidden", "secret")
        _make_file(source / "visible.md", "# Hello")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1
        assert files[0].source == source / "visible.md"

    def test_dotdir_excluded(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / ".theme" / "page.html", "<html>")
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1

    def test_config_file_excluded(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "site.conf", "title: Test")
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1
        assert files[0].source == source / "index.md"

    def test_config_in_subdir_not_excluded(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "sub" / "site.conf", "some content")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert len(files) == 1
        assert files[0].node_type == NodeType.STATIC

    def test_name_collision_markdown_wins(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "about.md", "# About")
        _make_file(source / "about.jpg", "fake image")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        md_files = [f for f in files if f.node_type == NodeType.MARKDOWN]
        img_files = [f for f in files if f.node_type == NodeType.IMAGE]
        static_files = [f for f in files if f.node_type == NodeType.STATIC]

        assert len(md_files) == 1
        assert len(img_files) == 0
        assert len(static_files) == 1
        assert static_files[0].source == source / "about.jpg"

    def test_nested_directories(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "news" / "index.md", "# News")
        _make_file(source / "news" / "photo.png", "fake")

        tree = scan(source, "site.conf")
        news = _find_child(tree, "news")
        # index.md collapses into news dir node
        assert news.node_type == NodeType.MARKDOWN
        assert news.source == source / "news" / "index.md"
        # photo.png is a child
        assert len(news.children) == 1
        assert news.children[0].source == source / "news" / "photo.png"

    def test_case_insensitive_extensions(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "photo.JPG", "fake")
        _make_file(source / "doc.MD", "# Hello")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        types = {f.node_type for f in files}
        assert NodeType.IMAGE in types
        assert NodeType.MARKDOWN in types

    def test_all_image_extensions(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        for ext in (".jpeg", ".jpg", ".webp", ".png"):
            _make_file(source / f"img{ext}", "fake")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        assert all(f.node_type == NodeType.IMAGE for f in files)
        assert len(files) == 4

    def test_collision_in_subdir(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "news" / "today.md", "# Today")
        _make_file(source / "news" / "today.jpg", "fake")

        tree = scan(source, "site.conf")
        files = _all_source_nodes(tree)
        md_files = [f for f in files if f.node_type == NodeType.MARKDOWN]
        static_files = [f for f in files if f.node_type == NodeType.STATIC]
        assert len(md_files) == 1
        assert len(static_files) == 1
        assert static_files[0].source == source / "news" / "today.jpg"

    def test_empty_source_dir(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()

        tree = scan(source, "site.conf")
        assert _all_source_nodes(tree) == []

    def test_index_md_collapses_into_directory(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "about" / "index.md", "# About")

        tree = scan(source, "site.conf")
        about = _find_child(tree, "about")
        assert about.node_type == NodeType.MARKDOWN
        assert about.source == source / "about" / "index.md"
        # No child named "index"
        assert all(c.name != "index" for c in about.children)

    def test_root_index_md_collapses(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "index.md", "# Home")

        tree = scan(source, "site.conf")
        assert tree.node_type == NodeType.MARKDOWN
        assert tree.source == source / "index.md"
        assert tree.children == []

    def test_container_dir_without_index(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "blog" / "post.md", "# Post")

        tree = scan(source, "site.conf")
        blog = _find_child(tree, "blog")
        assert blog.node_type is None
        assert blog.source is None
        assert len(blog.children) == 1

    def test_parent_pointers(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _make_file(source / "index.md", "# Home")
        _make_file(source / "news" / "post.md", "# Post")
        _make_file(source / "news" / "photo.jpg", "fake")

        tree = scan(source, "site.conf")
        assert tree.parent is None
        news = _find_child(tree, "news")
        assert news.parent is tree
        for child in news.children:
            assert child.parent is news
