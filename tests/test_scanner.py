import pytest
from pathlib import Path
from static_gallery.scanner import scan
from static_gallery.model import FileType, SourceDir, SourceFile


def _make_file(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _all_files(node):
    files = list(node.files)
    for child in node.children.values():
        files.extend(_all_files(child))
    return files


class TestScan:
    def test_markdown_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].file_type == FileType.MARKDOWN
        assert files[0].html_target == target / "index.html"
        assert files[0].asset_target is None

    def test_image_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "photo.jpg", "fake image")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].file_type == FileType.IMAGE
        assert files[0].html_target == target / "photo.html"
        assert files[0].asset_target == target / "photo.jpg"

    def test_static_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "styles.css", "body {}")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].file_type == FileType.STATIC
        assert files[0].asset_target == target / "styles.css"
        assert files[0].html_target is None

    def test_dotfile_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / ".hidden", "secret")
        _make_file(source / "visible.md", "# Hello")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].source_path == source / "visible.md"

    def test_dotdir_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / ".theme" / "page.html", "<html>")
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1

    def test_config_file_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "site.conf", "title: Test")
        _make_file(source / "index.md", "# Hello")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].source_path == source / "index.md"

    def test_config_in_subdir_not_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "sub" / "site.conf", "some content")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].file_type == FileType.STATIC

    def test_name_collision_markdown_wins(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "about.md", "# About")
        _make_file(source / "about.jpg", "fake image")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        md_files = [f for f in files if f.file_type == FileType.MARKDOWN]
        img_files = [f for f in files if f.file_type == FileType.IMAGE]
        static_files = [f for f in files if f.file_type == FileType.STATIC]

        assert len(md_files) == 1
        assert len(img_files) == 0
        assert len(static_files) == 1
        assert static_files[0].source_path == source / "about.jpg"
        assert static_files[0].asset_target == target / "about.jpg"

    def test_nested_directories(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "index.md", "# News")
        _make_file(source / "news" / "photo.png", "fake")

        tree = scan(source, target, "site.conf")
        assert "news" in tree.children
        news = tree.children["news"]
        assert len(news.files) == 2
        sources = {f.source_path for f in news.files}
        assert source / "news" / "index.md" in sources
        assert source / "news" / "photo.png" in sources

    def test_case_insensitive_extensions(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "photo.JPG", "fake")
        _make_file(source / "doc.MD", "# Hello")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        types = {f.file_type for f in files}
        assert FileType.IMAGE in types
        assert FileType.MARKDOWN in types

    def test_all_image_extensions(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        for ext in (".jpeg", ".jpg", ".webp", ".png"):
            _make_file(source / f"img{ext}", "fake")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert all(f.file_type == FileType.IMAGE for f in files)
        assert len(files) == 4

    def test_image_target_paths(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "photo.jpg", "fake")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        assert len(files) == 1
        assert files[0].html_target == target / "news" / "photo.html"
        assert files[0].asset_target == target / "news" / "photo.jpg"

    def test_collision_in_subdir(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "today.md", "# Today")
        _make_file(source / "news" / "today.jpg", "fake")

        tree = scan(source, target, "site.conf")
        files = _all_files(tree)
        md_files = [f for f in files if f.file_type == FileType.MARKDOWN]
        static_files = [f for f in files if f.file_type == FileType.STATIC]
        assert len(md_files) == 1
        assert len(static_files) == 1
        assert static_files[0].source_path == source / "news" / "today.jpg"

    def test_empty_source_dir(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()

        tree = scan(source, target, "site.conf")
        assert _all_files(tree) == []
