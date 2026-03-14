import argparse
import logging
import os

from static_gallery.config import StaticGalleryConfig
from static_gallery.renderer import Renderer
from static_gallery.scanner import Scanner

CLI_ARG_MAP = {
    "title": "site.title",
    "language": "site.language",
    "url": "site.url",
    "config": "config_path",
    "theme": "theme_path",
    "public": "public_path",
}


def main() -> int:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="static site and image gallery generator"
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="source path (default: current directory)",
    )
    parser.add_argument("--config", help="path to site.conf")
    parser.add_argument("--theme", help="path to theme directory")
    parser.add_argument("--public", help="path to output directory")
    parser.add_argument("--title", help="site title")
    parser.add_argument("--language", help="site language")
    parser.add_argument("--url", help="site URL")
    args = parser.parse_args()

    cli_args = {}
    for arg_name, config_key in CLI_ARG_MAP.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            cli_args[config_key] = value

    config = StaticGalleryConfig(cli_args=cli_args)

    if config.config_path:
        config.load_file(config.config_path)

    try:
        source_path = os.path.abspath(args.source)
        source_root = Scanner(config).scan(source_path)
        Renderer(config).render(source_root, source_path)
    except Exception as e:
        logging.getLogger(__name__).error("%s", e)
        return 1

    return 0
