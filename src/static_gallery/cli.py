import argparse
import functools
import logging
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

from static_gallery.config import Config
from static_gallery.builder import Builder
from static_gallery.scanner import Scanner

CLI_ARG_MAP = {
    "title": "site.title",
    "language": "site.language",
    "url": "site.url",
    "config": "config_path",
    "theme": "theme_path",
    "public": "public_path",
}


def _build_parser():
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
    parser.add_argument(
        "--serve", action="store_true", help="start a local HTTP server after build"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port for the HTTP server (default: 8000)",
    )
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO)

    args = _build_parser().parse_args()

    cli_args = {}
    for arg_name, config_key in CLI_ARG_MAP.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            cli_args[config_key] = value

    config = Config(cli_args=cli_args)

    if config.config_path:
        config.load_file(config.config_path)

    try:
        source_path = os.path.abspath(args.source)
        source_root = Scanner(config).scan(source_path)
        Builder(config).render(source_root, source_path)
    except Exception as e:
        logging.getLogger(__name__).error("%s", e)
        return 1

    if args.serve:
        _serve(os.path.abspath(config.public_path), args.port)

    return 0


def _serve(public_path, port):
    handler = functools.partial(SimpleHTTPRequestHandler, directory=public_path)
    server = HTTPServer(("", port), handler)
    print(f"Serving at http://localhost:{port} — press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
