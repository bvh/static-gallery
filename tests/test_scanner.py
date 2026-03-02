import pytest
from pathlib import Path
from static_gallery.scanner import scan, TaskType


def _make_file(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestScan:
    def test_markdown_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "index.md", "# Hello")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.MARKDOWN
        assert tasks[0].target_paths == [target / "index.html"]

    def test_image_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "photo.jpg", "fake image")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.IMAGE
        assert tasks[0].target_paths == [target / "photo.html", target / "photo.jpg"]

    def test_static_classified(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "styles.css", "body {}")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.STATIC
        assert tasks[0].target_paths == [target / "styles.css"]

    def test_dotfile_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / ".hidden", "secret")
        _make_file(source / "visible.md", "# Hello")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].source_path == source / "visible.md"

    def test_dotdir_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / ".theme" / "page.html", "<html>")
        _make_file(source / "index.md", "# Hello")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1

    def test_config_file_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "site.conf", "title: Test")
        _make_file(source / "index.md", "# Hello")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].source_path == source / "index.md"

    def test_config_in_subdir_not_excluded(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "sub" / "site.conf", "some content")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.STATIC

    def test_name_collision_markdown_wins(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "about.md", "# About")
        _make_file(source / "about.jpg", "fake image")

        tasks = scan(source, target, "site.conf")
        md_tasks = [t for t in tasks if t.task_type == TaskType.MARKDOWN]
        img_tasks = [t for t in tasks if t.task_type == TaskType.IMAGE]
        static_tasks = [t for t in tasks if t.task_type == TaskType.STATIC]

        assert len(md_tasks) == 1
        assert len(img_tasks) == 0
        assert len(static_tasks) == 1
        assert static_tasks[0].source_path == source / "about.jpg"
        assert static_tasks[0].target_paths == [target / "about.jpg"]

    def test_nested_directories(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "index.md", "# News")
        _make_file(source / "news" / "photo.png", "fake")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 2
        sources = {t.source_path for t in tasks}
        assert source / "news" / "index.md" in sources
        assert source / "news" / "photo.png" in sources

    def test_case_insensitive_extensions(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "photo.JPG", "fake")
        _make_file(source / "doc.MD", "# Hello")

        tasks = scan(source, target, "site.conf")
        types = {t.task_type for t in tasks}
        assert TaskType.IMAGE in types
        assert TaskType.MARKDOWN in types

    def test_all_image_extensions(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        for ext in (".jpeg", ".jpg", ".webp", ".png"):
            _make_file(source / f"img{ext}", "fake")

        tasks = scan(source, target, "site.conf")
        assert all(t.task_type == TaskType.IMAGE for t in tasks)
        assert len(tasks) == 4

    def test_image_target_paths(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "photo.jpg", "fake")

        tasks = scan(source, target, "site.conf")
        assert len(tasks) == 1
        assert tasks[0].target_paths == [
            target / "news" / "photo.html",
            target / "news" / "photo.jpg",
        ]

    def test_collision_in_subdir(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        _make_file(source / "news" / "today.md", "# Today")
        _make_file(source / "news" / "today.jpg", "fake")

        tasks = scan(source, target, "site.conf")
        md_tasks = [t for t in tasks if t.task_type == TaskType.MARKDOWN]
        static_tasks = [t for t in tasks if t.task_type == TaskType.STATIC]
        assert len(md_tasks) == 1
        assert len(static_tasks) == 1
        assert static_tasks[0].source_path == source / "news" / "today.jpg"

    def test_empty_source_dir(self, tmp_path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()

        tasks = scan(source, target, "site.conf")
        assert tasks == []
