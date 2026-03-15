import fnmatch
import html
import logging
import os
import re
import shlex

from static_gallery.node import NodeType, build_image_data

logger = logging.getLogger(__name__)

SHORTCODE_RE = re.compile(r"<<(.*?)>>")

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".css",
    ".html",
    ".htm",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".bash",
    ".rb",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".sql",
}


class ShortcodeProcessor:
    def __init__(self, root_node, source_path, env, resolve_url):
        self._root = root_node
        self._source_path = source_path
        self._env = env
        self._resolve_url = resolve_url
        self._index = self._build_index(root_node)

    def _build_index(self, root):
        index = {}
        self._walk_index(root, index)
        return index

    def _walk_index(self, node, index):
        rel = os.path.relpath(node.path, self._source_path)
        if rel != ".":
            index[rel] = node

        for img in node.images:
            img_rel = os.path.relpath(img.path, self._source_path)
            index[img_rel] = img

        for page in node.pages:
            page_rel = os.path.relpath(page.path, self._source_path)
            index[page_rel] = page

        for asset in node.assets:
            asset_rel = os.path.relpath(asset.path, self._source_path)
            index[asset_rel] = asset

        for d in node.dirs:
            self._walk_index(d, index)

    def process(self, text, current_node):
        def replace(match):
            inner = match.group(1).strip()
            if not inner:
                return match.group(0)
            if inner.startswith("/"):
                return self._handle_embed(inner, current_node)
            if re.match(r"^[a-zA-Z0-9_-]", inner):
                return self._handle_named(inner, current_node)
            return match.group(0)

        return SHORTCODE_RE.sub(replace, text)

    def _handle_embed(self, path, current_node):
        rel_path = path.lstrip("/")
        target = self._index.get(rel_path)
        if target is None:
            logger.warning("Shortcode target not found: %s", path)
            return html.escape(f"<<{path}>>")

        if target.type == NodeType.IMAGE:
            url = self._resolve_url(current_node, target, image_file=True)
            return f'<img src="{html.escape(url)}" alt="{html.escape(target.name)}">'

        ext = target.suffix.lower()
        if ext in CODE_EXTENSIONS:
            with open(target.path) as f:
                contents = f.read()
            lang = ext.lstrip(".")
            return (
                f'<pre><code class="language-{html.escape(lang)}">'
                f"{html.escape(contents)}</code></pre>"
            )

        url = self._resolve_url(current_node, target)
        return f'<a href="{html.escape(url)}">{html.escape(target.name)}</a>'

    def _handle_named(self, inner, current_node):
        try:
            parts = shlex.split(inner)
        except ValueError:
            logger.warning("Malformed shortcode: %s", inner)
            return html.escape(f"<<{inner}>>")
        name = parts[0]
        params = {}
        flags = set()
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value
            else:
                flags.add(part)

        if name == "gallery":
            return self._shortcode_gallery(current_node, params, flags)

        logger.warning("Unknown shortcode: %s", name)
        return html.escape(f"<<{inner}>>")

    def _shortcode_gallery(self, current_node, params, flags):
        images = list(current_node.images)

        filter_pattern = params.get("filter")
        if filter_pattern:
            images = [
                img for img in images if fnmatch.fnmatch(img.name, filter_pattern)
            ]

        sort_key = params.get("sort")
        if sort_key:
            images.sort(
                key=lambda img: (
                    sort_key not in img.metadata,
                    img.metadata.get(sort_key, ""),
                )
            )

        if "reverse" in flags:
            images.reverse()

        image_data = [build_image_data(img) for img in images]

        template = self._env.get_template("codes/gallery.html")
        return template.render(images=image_data)
