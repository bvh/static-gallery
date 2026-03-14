import logging
import os
import shutil

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from static_gallery.markdown import MarkdownRenderer

logger = logging.getLogger(__name__)


class Renderer:
    def __init__(self, config):
        self.config = config
        theme_path = config.theme_path
        if theme_path is None:
            theme_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "theme", "default"
            )
        theme_path = os.path.abspath(theme_path)
        self._theme_path = theme_path
        public_path = config.public_path or os.path.join(os.getcwd(), "public")
        self._public_path = os.path.abspath(public_path)
        self.env = Environment(
            loader=FileSystemLoader(theme_path),
            autoescape=True,
        )
        self._md = MarkdownRenderer()

    def render(self, root_node, source_path):
        self._source_path = os.path.abspath(source_path)
        os.makedirs(self._public_path, exist_ok=True)
        logger.info("Rendering site to %s", self._public_path)
        self._render_node(root_node)
        self._copy_theme_assets()
        logger.info("Site rendered successfully")

    def _render_node(self, node):
        output_rel = self._get_output_path(node, self._source_path)
        output_abs = os.path.join(self._public_path, output_rel)
        os.makedirs(os.path.dirname(output_abs), exist_ok=True)

        template_name = self._get_template_name(node)
        template = self.env.get_template(template_name)

        page_ctx = self._build_page_context(node)
        html = template.render(site=self.config.site, page=page_ctx)

        with open(output_abs, "w") as f:
            f.write(html)

        # Copy images
        for img in node.images:
            img_rel = os.path.relpath(img.path, self._source_path)
            img_dest = os.path.join(self._public_path, img_rel)
            os.makedirs(os.path.dirname(img_dest), exist_ok=True)
            shutil.copy2(img.path, img_dest)

        # Copy static assets
        for asset in node.assets:
            asset_rel = os.path.relpath(asset.path, self._source_path)
            asset_dest = os.path.join(self._public_path, asset_rel)
            os.makedirs(os.path.dirname(asset_dest), exist_ok=True)
            shutil.copy2(asset.path, asset_dest)

        # Recurse into child pages (MARKDOWN nodes)
        for page in node.pages:
            self._render_node(page)

        # Recurse into child directories
        for d in node.dirs:
            self._render_node(d)

    def _get_output_path(self, node, source_path):
        if node.type == "HOME":
            return "index.html"
        elif node.type == "MARKDOWN":
            rel = os.path.relpath(node.path, source_path)
            stem = os.path.splitext(rel)[0]
            return os.path.join(stem, "index.html")
        else:
            rel = os.path.relpath(node.path, source_path)
            return os.path.join(rel, "index.html")

    def _get_template_name(self, node):
        if node.type == "GALLERY":
            return "_gallery.html"
        if node.type == "DIRECTORY" and not node.text:
            return "_directory.html"
        return "_default.html"

    def _build_page_context(self, node):
        md_path = node.get_markdown_path()
        title = None
        content = ""

        if md_path and os.path.exists(md_path):
            result = self._md.render_file(md_path, remove_title=True)
            title = result.title
            content = Markup(result.html)

        if not title:
            title = node.stem if node.type == "MARKDOWN" else node.name

        # Build image list with relative URLs
        images = []
        for img in node.images:
            rel = os.path.relpath(img.path, node.path)
            images.append({"name": img.name, "url": rel})

        # Build page list
        pages = []
        for page in node.pages:
            pages.append({"name": page.stem, "url": page.stem + "/"})

        # Build directory list
        dirs = []
        for d in node.dirs:
            dirs.append({"name": d.name, "url": d.name + "/"})

        return {
            "title": title,
            "content": content,
            "images": images,
            "pages": pages,
            "dirs": dirs,
        }

    def _copy_theme_assets(self):
        for dirpath, dirnames, filenames in os.walk(self._theme_path):
            # Skip underscore-prefixed directories
            dirnames[:] = [d for d in dirnames if not d.startswith("_")]
            for filename in filenames:
                if filename.startswith("_"):
                    continue
                src = os.path.join(dirpath, filename)
                rel = os.path.relpath(src, self._theme_path)
                dest = os.path.join(self._public_path, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
