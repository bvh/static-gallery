import logging

from static_gallery.config import Config


def test_defaults():
    config = Config()
    assert config.get("site.language") == "en-us"


def test_cli_precedence():
    config = Config(cli_args={"site.title": "CLI Title"})
    assert config.get("site.title") == "CLI Title"


def test_env_var_loading(monkeypatch):
    monkeypatch.setenv("STATIC_GALLERY_SITE_TITLE", "Env Title")
    config = Config()
    assert config.get("site.title") == "Env Title"


def test_env_overrides_config_file(monkeypatch, tmp_path):
    monkeypatch.setenv("STATIC_GALLERY_SITE_TITLE", "Env Title")
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: File Title\n")
    config = Config()
    config.load_file(str(conf))
    assert config.get("site.title") == "Env Title"


def test_config_file_parsing(tmp_path):
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: My Site\nsite.language: fr\n")
    config = Config()
    config.load_file(str(conf))
    assert config.get("site.title") == "My Site"
    assert config.get("site.language") == "fr"


def test_config_file_comments_and_blanks(tmp_path):
    conf = tmp_path / "site.conf"
    conf.write_text("# comment\n\nsite.title: My Site\n\n# another comment\n")
    config = Config()
    config.load_file(str(conf))
    assert config.get("site.title") == "My Site"


def test_config_file_malformed_line(tmp_path, caplog):
    conf = tmp_path / "site.conf"
    conf.write_text("site.title My Site\nsite.language: fr\n")
    config = Config()
    with caplog.at_level(logging.WARNING):
        config.load_file(str(conf))
    assert config.get("site.title") is None
    assert config.get("site.language") == "fr"
    assert "Skipping malformed config line" in caplog.text


def test_config_file_invalid_keys(tmp_path, caplog):
    conf = tmp_path / "site.conf"
    conf.write_text("invalid key!: value\nsite.title: Good\n")
    config = Config()
    with caplog.at_level(logging.WARNING):
        config.load_file(str(conf))
    assert config.get("site.title") == "Good"
    assert "Skipping invalid config key" in caplog.text


def test_config_file_colon_in_value(tmp_path):
    conf = tmp_path / "site.conf"
    conf.write_text("site.url: https://example.com\n")
    config = Config()
    config.load_file(str(conf))
    assert config.get("site.url") == "https://example.com"


def test_config_file_value_with_hash(tmp_path):
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: My # Cool Site\n")
    config = Config()
    config.load_file(str(conf))
    assert config.get("site.title") == "My # Cool Site"


def test_site_property():
    config = Config(cli_args={"site.title": "CLI Title"})
    site = config.site
    assert site["title"] == "CLI Title"
    assert site["language"] == "en-us"


def test_convenience_properties():
    config = Config(
        cli_args={
            "config_path": "/tmp/site.conf",
            "theme_path": "/tmp/theme",
            "public_path": "/tmp/public",
        }
    )
    assert config.config_path == "/tmp/site.conf"
    assert config.theme_path == "/tmp/theme"
    assert config.public_path == "/tmp/public"


def test_warning_on_env_override(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv("STATIC_GALLERY_SITE_TITLE", "Env Title")
    conf = tmp_path / "site.conf"
    conf.write_text("site.title: File Title\n")
    config = Config()
    with caplog.at_level(logging.WARNING):
        config.load_file(str(conf))
    assert "already set by environment variable" in caplog.text
