from static_gallery import scanner
from static_gallery.config import StaticGalleryConfig
from static_gallery.scanner import scan


def test_scan_works_without_config(tmp_path):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    root = scan(str(tmp_path))
    assert root.type == "HOME"


def test_scan_with_config_loads_site_conf(tmp_path):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: My Site\n")
    config = StaticGalleryConfig()
    scan(str(tmp_path), config=config)
    assert config.get("site.title") == "My Site"


def test_process_config_removed():
    assert not hasattr(scanner, "process_config")
