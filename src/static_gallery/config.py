import logging
import os
import re

logger = logging.getLogger(__name__)

ENV_MAP = {
    "STATIC_GALLERY_SITE_TITLE": "site.title",
    "STATIC_GALLERY_SITE_LANGUAGE": "site.language",
    "STATIC_GALLERY_SITE_URL": "site.url",
    "STATIC_GALLERY_CONFIG": "config_path",
    "STATIC_GALLERY_THEME": "theme_path",
    "STATIC_GALLERY_PUBLIC": "public_path",
}

KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_.\-]+$")


class StaticGalleryConfig:
    def __init__(self, cli_args=None):
        self._defaults = {
            "site.language": "en-us",
        }
        self._inferred = {}
        self._file = {}
        self._env = {}
        self._cli = {}

        self._load_env()

        if cli_args:
            self._cli.update(cli_args)

    def _load_env(self):
        for env_name, key in ENV_MAP.items():
            value = os.environ.get(env_name)
            if value is not None:
                self._env[key] = value

    def load_file(self, path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    logger.warning("Skipping malformed config line: %s", line)
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if not KEY_PATTERN.match(key):
                    logger.warning("Skipping invalid config key: %s", key)
                    continue
                if key in self._env:
                    logger.warning(
                        "Config file key '%s' is already set by environment variable",
                        key,
                    )
                self._file[key] = value

    def set_inferred(self, key, value):
        self._inferred[key] = value

    def get(self, key, default=None):
        for layer in (self._cli, self._env, self._file, self._inferred, self._defaults):
            if key in layer:
                return layer[key]
        return default

    @property
    def site(self):
        result = {}
        seen = set()
        for layer in (
            self._cli,
            self._env,
            self._file,
            self._inferred,
            self._defaults,
        ):
            for key, value in layer.items():
                if key.startswith("site.") and key not in seen:
                    short_key = key[len("site.") :]
                    result[short_key] = value
                    seen.add(key)
        return result

    @property
    def config_path(self):
        return self.get("config_path")

    @property
    def theme_path(self):
        return self.get("theme_path")

    @property
    def public_path(self):
        return self.get("public_path")
