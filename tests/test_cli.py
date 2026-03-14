import sys

from static_gallery.cli import main


def test_cli_title_arg(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    monkeypatch.setattr(sys, "argv", ["gallery", str(tmp_path), "--title", "Foo"])
    rv = main()
    assert rv == 0


def test_cli_args_optional(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    monkeypatch.setattr(sys, "argv", ["gallery", str(tmp_path)])
    rv = main()
    assert rv == 0
