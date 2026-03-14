import sys
from unittest.mock import patch, MagicMock

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


def test_serve_starts_server_with_correct_directory_and_port(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    public = tmp_path / "output"
    monkeypatch.setattr(
        sys, "argv", ["gallery", str(tmp_path), "--serve", "--public", str(public)]
    )
    mock_server = MagicMock()
    with patch("static_gallery.cli.HTTPServer", return_value=mock_server) as mock_cls:
        main()
    addr, handler_partial = mock_cls.call_args[0]
    assert addr == ("", 8000)
    assert handler_partial.keywords["directory"] == str(public)


def test_serve_custom_port(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    monkeypatch.setattr(
        sys, "argv", ["gallery", str(tmp_path), "--serve", "--port", "3000"]
    )
    mock_server = MagicMock()
    with patch("static_gallery.cli.HTTPServer", return_value=mock_server) as mock_cls:
        main()
    addr, _ = mock_cls.call_args[0]
    assert addr == ("", 3000)


def test_no_serve_no_server(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    monkeypatch.setattr(sys, "argv", ["gallery", str(tmp_path)])
    with patch("static_gallery.cli.HTTPServer") as mock_cls:
        main()
    mock_cls.assert_not_called()


def test_serve_keyboard_interrupt_exits_cleanly(tmp_path, monkeypatch):
    index = tmp_path / "index.md"
    index.write_text("# Hello")
    monkeypatch.setattr(sys, "argv", ["gallery", str(tmp_path), "--serve"])
    mock_server = MagicMock()
    mock_server.serve_forever.side_effect = KeyboardInterrupt
    with patch("static_gallery.cli.HTTPServer", return_value=mock_server):
        rv = main()
    assert rv == 0
    mock_server.server_close.assert_called_once()
