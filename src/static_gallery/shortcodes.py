import fnmatch
import html
import logging
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
    def __init__(self, index, env, resolve_url):
        self._index = index
        self._env = env
        self._resolve_url = resolve_url

    def process(self, text, current_node):
        def replace(match):
            inner = match.group(1).strip()
            if not inner:
                return match.group(0)
            if inner.startswith("/"):
                return self._handle_embed(inner, current_node)
            if re.match(r"^[a-zA-Z0-9_-]", inner):
                first_token = inner.split()[0]
                # Route to embed if the token looks like a file path (contains
                # '.' or '/').  This means named shortcodes must not contain
                # dots — revisit this heuristic if a dotted name is ever needed.
                if "." in first_token or "/" in first_token:
                    return self._handle_embed(inner, current_node)
                return self._handle_named(inner, current_node)
            return match.group(0)

        return SHORTCODE_RE.sub(replace, text)

    def _handle_embed(self, path, current_node):
        target = self._index.resolve(path)

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

        sort_key = params.get("sort", "datetime")
        if sort_key:
            images.sort(
                key=lambda img: (
                    getattr(img.metadata, sort_key, None) is None,
                    getattr(img.metadata, sort_key, "") or "",
                )
            )

        if "reverse" in flags:
            images.reverse()

        image_data = [build_image_data(img) for img in images]

        template = self._env.get_template("codes/gallery.html")
        html = template.render(images=image_data)
        # Collapse blank lines so markdown-it doesn't terminate HTML blocks
        # mid-output (blank lines end CommonMark HTML blocks, causing
        # indented <li> elements to be parsed as code blocks).
        return re.sub(r"\n\s*\n", "\n", html)
