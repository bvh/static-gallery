import pytest

from static_gallery import scanner
from static_gallery.config import Config
from static_gallery.scanner import Scanner


def test_scan_works_without_config(tmp_path):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    site = Scanner().scan(str(tmp_path))
    assert site.root.type == "HOME"


def test_scan_with_config_loads_site_conf(tmp_path):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: My Site\n")
    config = Config()
    Scanner(config).scan(str(tmp_path))
    assert config.get("site.title") == "My Site"


def test_process_config_removed():
    assert not hasattr(scanner, "process_config")
    assert hasattr(scanner, "Scanner")
    assert not hasattr(scanner, "scan")


def test_scan_non_directory_raises(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hello")
    with pytest.raises(ValueError, match="not a directory"):
        Scanner().scan(str(f))


def test_index_md_sets_parent_text(tmp_path):
    index = tmp_path / "index.md"
    index.write_text("# Home")
    site = Scanner().scan(str(tmp_path))
    assert site.root.index_path == str(index)
    # index.md should not appear as a separate page node
    assert len(site.root.pages) == 0


def test_dotfiles_are_skipped(tmp_path):
    (tmp_path / "index.md").write_text("# Hi")
    (tmp_path / ".hidden").write_text("secret")
    (tmp_path / ".hiddendir").mkdir()
    (tmp_path / ".hiddendir" / "file.txt").write_text("stuff")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.pages) == 0
    assert len(site.root.assets) == 0
    assert len(site.root.dirs) == 0


def test_symlinks_are_skipped(tmp_path):
    (tmp_path / "index.md").write_text("# Hi")
    real = tmp_path / "real.md"
    real.write_text("# Real")
    link = tmp_path / "link.md"
    link.symlink_to(real)
    site = Scanner().scan(str(tmp_path))
    # real.md is counted, link.md is not
    assert len(site.root.pages) == 1
    assert site.root.pages[0].name == "real.md"


def test_markdown_files_classified(tmp_path):
    (tmp_path / "page.md").write_text("# Page")
    (tmp_path / "doc.markdown").write_text("# Doc")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.pages) == 2
    types = {p.type for p in site.root.pages}
    assert types == {"PAGE"}


def test_image_files_classified(tmp_path):
    for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        (tmp_path / f"img{ext}").write_bytes(b"\x00")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.images) == 5
    assert all(i.type == "IMAGE" for i in site.root.images)


def test_static_files_classified(tmp_path):
    (tmp_path / "style.css").write_text("body {}")
    (tmp_path / "script.js").write_text("console.log()")
    (tmp_path / "data.json").write_text("{}")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.assets) == 3
    assert all(a.type == "STATIC" for a in site.root.assets)


def test_subdirectory_classified_as_directory(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "page.md").write_text("# Sub page")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.dirs) == 1
    assert site.root.dirs[0].type == "DIRECTORY"
    assert site.root.dirs[0].name == "subdir"


def test_gallery_directory(tmp_path):
    gallery = tmp_path / "photos"
    gallery.mkdir()
    (gallery / "a.jpg").write_bytes(b"\x00")
    (gallery / "b.png").write_bytes(b"\x00")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.dirs) == 1
    assert site.root.dirs[0].type == "GALLERY"


def test_mixed_directory_not_gallery(tmp_path):
    sub = tmp_path / "mixed"
    sub.mkdir()
    (sub / "photo.jpg").write_bytes(b"\x00")
    (sub / "readme.md").write_text("# Hi")
    site = Scanner().scan(str(tmp_path))
    assert site.root.dirs[0].type == "DIRECTORY"


def test_empty_directory_skipped(tmp_path):
    (tmp_path / "empty").mkdir()
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.dirs) == 0


def test_empty_directory_with_only_dotfiles_skipped(tmp_path):
    sub = tmp_path / "seemsempty"
    sub.mkdir()
    (sub / ".gitkeep").write_text("")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.dirs) == 0


def test_recursive_scanning(tmp_path):
    # root/
    #   index.md
    #   sub/
    #     page.md
    #     deep/
    #       photo.jpg
    (tmp_path / "index.md").write_text("# Root")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "page.md").write_text("# Sub")
    deep = sub / "deep"
    deep.mkdir()
    (deep / "photo.jpg").write_bytes(b"\x00")

    site = Scanner().scan(str(tmp_path))
    assert site.root.type == "HOME"
    assert site.root.index_path is not None
    assert len(site.root.dirs) == 1

    sub_node = site.root.dirs[0]
    assert sub_node.type == "DIRECTORY"
    assert len(sub_node.pages) == 1
    assert len(sub_node.dirs) == 1

    deep_node = sub_node.dirs[0]
    assert deep_node.type == "GALLERY"
    assert len(deep_node.images) == 1


def test_site_conf_not_loaded_in_subdirectory(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "site.conf").write_text("site.title: Nested\n")
    (sub / "page.md").write_text("# Page")
    config = Config()
    site = Scanner(config).scan(str(tmp_path))
    # site.conf in subdir should be treated as a static asset, not loaded
    assert config.get("site.title") is None
    assert len(site.root.dirs[0].assets) == 1


def test_site_conf_skipped_when_config_path_set(tmp_path):
    (tmp_path / "site.conf").write_text("site.title: From File\n")
    (tmp_path / "index.md").write_text("# Hi")
    config = Config(cli_args={"config_path": "/some/other.conf"})
    Scanner(config).scan(str(tmp_path))
    # site.conf should not be loaded because config_path is already set
    assert config.get("site.title") is None


def test_index_md_case_insensitive(tmp_path):
    index = tmp_path / "INDEX.MD"
    index.write_text("# Upper")
    site = Scanner().scan(str(tmp_path))
    assert site.root.index_path == str(index)
    assert len(site.root.pages) == 0


def test_child_nodes_have_parent_set(tmp_path):
    (tmp_path / "page.md").write_text("# Page")
    site = Scanner().scan(str(tmp_path))
    assert site.root.pages[0].parent is site.root


def test_paired_markdown_sets_content_path(tmp_path):
    """photo.md paired with photo.jpg sets content_path on the IMAGE node."""
    (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff")
    (tmp_path / "photo.md").write_text("# My Photo\n\nA beautiful sunset.")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.images) == 1
    assert len(site.root.pages) == 0
    assert site.root.images[0].content_path == str(tmp_path / "photo.md")


def test_unpaired_markdown_remains_page(tmp_path):
    """Markdown without a matching image stem stays as a page."""
    (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff")
    (tmp_path / "about.md").write_text("# About")
    site = Scanner().scan(str(tmp_path))
    assert len(site.root.images) == 1
    assert len(site.root.pages) == 1
    assert site.root.pages[0].name == "about.md"


def test_paired_markdown_gallery_classification(tmp_path):
    """Directory with only images + paired markdown is still a GALLERY."""
    gallery = tmp_path / "photos"
    gallery.mkdir()
    (gallery / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (gallery / "b.jpg").write_bytes(b"\xff\xd8\xff")
    (gallery / "a.md").write_text("# Photo A")
    site = Scanner().scan(str(tmp_path))
    assert site.root.dirs[0].type == "GALLERY"
    assert len(site.root.dirs[0].images) == 2
    assert len(site.root.dirs[0].pages) == 0


def test_paired_markdown_mixed_directory(tmp_path):
    """Paired markdown + unpaired markdown = DIRECTORY not GALLERY."""
    sub = tmp_path / "mixed"
    sub.mkdir()
    (sub / "photo.jpg").write_bytes(b"\xff\xd8\xff")
    (sub / "photo.md").write_text("# Photo")
    (sub / "about.md").write_text("# About")
    site = Scanner().scan(str(tmp_path))
    assert site.root.dirs[0].type == "DIRECTORY"


def test_index_md_not_paired_with_image(tmp_path):
    """index.md is consumed as container text, not paired with index.jpg."""
    (tmp_path / "index.md").write_text("# Home")
    (tmp_path / "index.jpg").write_bytes(b"\xff\xd8\xff")
    site = Scanner().scan(str(tmp_path))
    assert site.root.index_path == str(tmp_path / "index.md")
    assert len(site.root.images) == 1
    assert site.root.images[0].content_path is None
