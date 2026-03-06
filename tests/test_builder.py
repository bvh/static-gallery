import pytest
from pathlib import Path
from static_gallery.builder import build
from static_gallery.model import FileType, SourceDir, SourceFile


PAGE_TEMPLATE = "<html><head><title>{{ page.title }}</title></head><body>{{ content }}</body></html>"
IMAGE_TEMPLATE = "<html><head><title>{{ page.title }}</title></head><body><img src=\"{{ content }}\"></body></html>"


def _setup_theme(source, page=PAGE_TEMPLATE, image=IMAGE_TEMPLATE):
    theme = source / ".theme"
    theme.mkdir(parents=True, exist_ok=True)
    (theme / "page.html").write_text(page)
    (theme / "image.html").write_text(image)


def _site_config():
    return {"title": "Test Site", "url": "https://example.com/", "language": "en-us"}


def _wrap(files):
    return SourceDir(rel_path=Path("."), files=files)


class TestBuildMarkdown:
    def test_renders_through_template(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        md_file = source / "index.md"
        md_file.write_text("Title: Home\n\nHello **world**.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("index.md"),
            html_target=target / "index.html",
        )])
        build(tree, _site_config(), source, target)

        output = (target / "index.html").read_text()
        assert "<title>Home</title>" in output
        assert "<strong>world</strong>" in output

    def test_template_variables(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        tpl = "site={{ site.title }}|page={{ page.author }}|content={{ content }}"
        _setup_theme(source, page=tpl)

        md_file = source / "test.md"
        md_file.write_text("Author: Jane\n\nHi.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("test.md"),
            html_target=target / "test.html",
        )])
        build(tree, _site_config(), source, target)

        output = (target / "test.html").read_text()
        assert "site=Test Site" in output
        assert "page=Jane" in output
        assert "content=" in output

    def test_type_override(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        md_file = source / "gallery.md"
        md_file.write_text("Type: image\nTitle: Gallery\n\nSome content.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("gallery.md"),
            html_target=target / "gallery.html",
        )])
        build(tree, _site_config(), source, target)

        output = (target / "gallery.html").read_text()
        assert "<img src=" in output

    def test_no_front_matter(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        md_file = source / "plain.md"
        md_file.write_text("Just some text.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("plain.md"),
            html_target=target / "plain.html",
        )])
        build(tree, _site_config(), source, target)

        output = (target / "plain.html").read_text()
        assert "Just some text." in output


class TestBuildImage:
    def test_renders_through_template(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        img_file = source / "photo.jpg"
        img_file.write_bytes(b"fake image data")

        tree = _wrap([SourceFile(
            FileType.IMAGE, img_file, Path("photo.jpg"),
            html_target=target / "photo.html",
            asset_target=target / "photo.jpg",
        )])
        build(tree, _site_config(), source, target)

        html = (target / "photo.html").read_text()
        assert "<title>Photo</title>" in html
        assert 'src="photo.jpg"' in html

        assert (target / "photo.jpg").read_bytes() == b"fake image data"

    def test_title_from_stem(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        img_file = source / "my-cool_photo.png"
        img_file.write_bytes(b"fake")

        tree = _wrap([SourceFile(
            FileType.IMAGE, img_file, Path("my-cool_photo.png"),
            html_target=target / "my-cool_photo.html",
            asset_target=target / "my-cool_photo.png",
        )])
        build(tree, _site_config(), source, target)

        html = (target / "my-cool_photo.html").read_text()
        assert "<title>My Cool Photo</title>" in html


class TestBuildStatic:
    def test_copies_file(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        css_file = source / "styles.css"
        css_file.write_text("body { color: red; }")

        tree = _wrap([SourceFile(
            FileType.STATIC, css_file, Path("styles.css"),
            asset_target=target / "styles.css",
        )])
        build(tree, _site_config(), source, target)

        assert (target / "styles.css").read_text() == "body { color: red; }"

    def test_creates_parent_dirs(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        js_file = source / "assets" / "app.js"
        js_file.parent.mkdir(parents=True)
        js_file.write_text("console.log('hi')")

        tree = _wrap([SourceFile(
            FileType.STATIC, js_file, Path("assets/app.js"),
            asset_target=target / "assets" / "app.js",
        )])
        build(tree, _site_config(), source, target)

        assert (target / "assets" / "app.js").read_text() == "console.log('hi')"


class TestTargetSync:
    def test_stale_file_removed(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        stale = target / "old.html"
        stale.write_text("stale")

        md_file = source / "index.md"
        md_file.write_text("Title: Home\n\nHello.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("index.md"),
            html_target=target / "index.html",
        )])
        build(tree, _site_config(), source, target)

        assert not stale.exists()
        assert (target / "index.html").exists()

    def test_empty_dirs_cleaned(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        stale_dir = target / "old"
        stale_dir.mkdir()
        (stale_dir / "stale.html").write_text("stale")

        md_file = source / "index.md"
        md_file.write_text("Title: Home\n\nHello.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("index.md"),
            html_target=target / "index.html",
        )])
        build(tree, _site_config(), source, target)

        assert not stale_dir.exists()

    def test_target_root_not_removed(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        build(_wrap([]), _site_config(), source, target)

        assert target.exists()


class TestBuildErrors:
    def test_missing_template_exits(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        md_file = source / "index.md"
        md_file.write_text("Title: Home\n\nHello.")

        tree = _wrap([SourceFile(
            FileType.MARKDOWN, md_file, Path("index.md"),
            html_target=target / "index.html",
        )])
        with pytest.raises(SystemExit):
            build(tree, _site_config(), source, target)

    def test_unreadable_source_exits(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        _setup_theme(source)

        missing = source / "gone.md"
        tree = _wrap([SourceFile(
            FileType.MARKDOWN, missing, Path("gone.md"),
            html_target=target / "gone.html",
        )])
        with pytest.raises(SystemExit):
            build(tree, _site_config(), source, target)
