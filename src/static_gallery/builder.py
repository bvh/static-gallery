import importlib.metadata
import importlib.resources
import logging
import os
import shutil

from jinja2 import Environment, FileSystemLoader, PackageLoader
from markupsafe import Markup

from static_gallery.markdown import MarkdownRenderer
from static_gallery.node import NodeType, build_image_data
from static_gallery.shortcodes import ShortcodeProcessor

logger = logging.getLogger(__name__)


class Builder:
    def __init__(self, config):
        self.config = config
        theme_path = config.theme_path
        if theme_path is None:
            self._bundled_theme = True
            loader = PackageLoader("static_gallery", "themes/default")
        else:
            self._bundled_theme = False
            theme_path = os.path.abspath(theme_path)
            self._theme_path = theme_path
            loader = FileSystemLoader(theme_path)
        public_path = config.public_path
        self._public_path = os.path.abspath(public_path)
        self.env = Environment(
            loader=loader,
            autoescape=True,
        )
        self._md = MarkdownRenderer()
        self._shortcodes = None
        meta = importlib.metadata.metadata("static-gallery")
        package = meta["Name"]
        self._generator = {
            "name": package.replace("-", " ").title(),
            "package": package,
            "version": meta["Version"],
        }

    def render(self, site):
        self._source_path = site.source_path
        path_map = {}
        self._collect_output_paths(site.root, path_map)
        self._check_collisions(path_map)
        self._shortcodes = ShortcodeProcessor(site.index, self.env, self._resolve_url)
        os.makedirs(self._public_path, exist_ok=True)
        logger.info("Rendering site to %s", self._public_path)
        self._render_node(site.root)
        self._copy_theme_assets()
        logger.info("Site rendered successfully")

    def _collect_output_paths(self, node, path_map):
        # Rendered HTML for this node
        output_rel = self._get_output_path(node, self._source_path)
        source_rel = os.path.relpath(node.path, self._source_path)
        path_map.setdefault(output_rel, []).append(source_rel)

        # Image nodes get an HTML page + relocated image file
        for img in node.images:
            self._collect_output_paths(img, path_map)
            img_file_rel = self._get_image_file_output_path(img, self._source_path)
            img_source_rel = os.path.relpath(img.path, self._source_path)
            path_map.setdefault(img_file_rel, []).append(img_source_rel)

        # Copied static assets
        for asset in node.assets:
            asset_rel = os.path.relpath(asset.path, self._source_path)
            path_map.setdefault(asset_rel, []).append(asset_rel)

        for page in node.pages:
            self._collect_output_paths(page, path_map)

        for d in node.dirs:
            self._collect_output_paths(d, path_map)

    def _check_collisions(self, path_map):
        """Raise an error if any output path has multiple distinct sources."""
        collisions = {}
        for output_path, sources in path_map.items():
            unique = list(dict.fromkeys(sources))
            if len(unique) > 1:
                collisions[output_path] = unique
        if collisions:
            lines = []
            for output_path, sources in collisions.items():
                sources_str = ", ".join(sources)
                lines.append(f"  {output_path} <- {sources_str}")
            msg = "Output path collision detected:\n" + "\n".join(lines)
            raise RuntimeError(msg)

    def _render_node(self, node):
        output_rel = self._get_output_path(node, self._source_path)
        output_abs = os.path.join(self._public_path, output_rel)
        os.makedirs(os.path.dirname(output_abs), exist_ok=True)

        template = self.env.get_template(node.template_name)

        page_ctx = self._build_page_context(node)
        html = template.render(
            site=self.config.site, page=page_ctx, generator=self._generator
        )

        with open(output_abs, "w") as f:
            f.write(html)

        # Render image pages and copy image files
        for img in node.images:
            self._render_node(img)
            img_file_rel = self._get_image_file_output_path(img, self._source_path)
            img_file_abs = os.path.join(self._public_path, img_file_rel)
            os.makedirs(os.path.dirname(img_file_abs), exist_ok=True)
            shutil.copy2(img.path, img_file_abs)

        # Copy static assets
        for asset in node.assets:
            asset_rel = os.path.relpath(asset.path, self._source_path)
            asset_dest = os.path.join(self._public_path, asset_rel)
            os.makedirs(os.path.dirname(asset_dest), exist_ok=True)
            shutil.copy2(asset.path, asset_dest)

        # Recurse into child pages (PAGE nodes)
        for page in node.pages:
            self._render_node(page)

        # Recurse into child directories
        for d in node.dirs:
            self._render_node(d)

    def _get_output_path(self, node, source_path):
        if node.type == NodeType.HOME:
            return "index.html"
        elif node.type in (NodeType.PAGE, NodeType.IMAGE):
            rel = os.path.relpath(node.path, source_path)
            stem = os.path.splitext(rel)[0]
            return os.path.join(stem, "index.html")
        else:
            rel = os.path.relpath(node.path, source_path)
            return os.path.join(rel, "index.html")

    def _get_image_file_output_path(self, node, source_path):
        rel = os.path.relpath(node.path, source_path)
        stem = os.path.splitext(rel)[0]
        return os.path.join(stem, node.name)

    def _resolve_url(self, current_node, target_node, image_file=False):
        current_output = self._get_output_path(current_node, self._source_path)
        current_dir = os.path.dirname(current_output)
        if image_file and target_node.type == NodeType.IMAGE:
            target_output = self._get_image_file_output_path(
                target_node, self._source_path
            )
        elif target_node.type == NodeType.STATIC:
            target_output = os.path.relpath(target_node.path, self._source_path)
        else:
            target_output = self._get_output_path(target_node, self._source_path)
        return os.path.relpath(target_output, current_dir)

    def _build_page_context(self, node):
        md_path = node.get_markdown_path()
        title = None
        content = ""

        if md_path and os.path.exists(md_path):
            with open(md_path) as f:
                text = f.read()
            text = self._shortcodes.process(text, node)
            result = self._md.render(text, remove_title=True)
            title = result.title
            content = Markup(result.html)

        if not title:
            title = node.title_fallback

        ctx = {
            "title": title,
            "content": content,
        }

        if node.type == NodeType.IMAGE:
            # Single image page context
            image_data = dict(node.metadata)
            image_data["name"] = node.name
            image_data["url"] = node.name
            ctx["image"] = image_data
        else:
            # Build image list with links to image pages
            ctx["images"] = [build_image_data(img) for img in node.images]

        # Build page list
        pages = []
        for page in node.pages:
            pages.append({"name": page.stem, "url": page.stem + "/"})

        # Build directory list
        dirs = []
        for d in node.dirs:
            dirs.append({"name": d.name, "url": d.name + "/"})

        ctx["pages"] = pages
        ctx["dirs"] = dirs

        return ctx

    def _copy_theme_assets(self):
        if self._bundled_theme:
            self._copy_bundled_theme_assets()
        else:
            self._copy_custom_theme_assets()

    def _copy_bundled_theme_assets(self):
        static_dir = importlib.resources.files("static_gallery").joinpath(
            "themes/default/static"
        )
        if static_dir.is_dir():
            self._copy_bundled_dir(static_dir, self._public_path)

    def _copy_bundled_dir(self, resource_dir, dest_dir):
        for item in resource_dir.iterdir():
            if item.is_file():
                dest = os.path.join(dest_dir, item.name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(item.read_bytes())
            elif item.is_dir():
                self._copy_bundled_dir(item, os.path.join(dest_dir, item.name))

    def _copy_custom_theme_assets(self):
        static_dir = os.path.join(self._theme_path, "static")
        if not os.path.isdir(static_dir):
            return
        for dirpath, dirnames, filenames in os.walk(static_dir):
            for filename in filenames:
                src = os.path.join(dirpath, filename)
                rel = os.path.relpath(src, static_dir)
                dest = os.path.join(self._public_path, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
