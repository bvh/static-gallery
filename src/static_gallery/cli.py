import argparse
import os

from static_gallery.scanner import scan


def main() -> int:
    rv = 0

    parser = argparse.ArgumentParser(
        description="static site and image gallery generator"
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="source path (default: current directory)",
    )
    args = parser.parse_args()

    source_path = os.path.abspath(args.source)
    print(f"scanning {source_path}")
    source_root = scan(source_path)
    print(source_root)

    return rv
