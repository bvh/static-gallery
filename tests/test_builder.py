import os

import pytest

from static_gallery.builder import Builder
from static_gallery.config import Config
from static_gallery.index import SuffixIndex
from static_gallery.metadata import Metadata
from static_gallery.node import Node
from static_gallery.scanner import Scanner
from static_gallery.shortcodes import ShortcodeProcessor
from tests.helpers import make_metadata


def _make_theme(tmp_path, **templates):
    """Create a theme directory with required templates.

    Any template can be overridden via keyword args, e.g.
    _make_theme(tmp_path, default="custom {{ page.title }}")
    """
    theme = tmp_path / "theme"
    theme.mkdir(exist_ok=True)
    defaults = {
        "default": "{{ page.title }}",
        "home": "{{ page.title }}",
        "page": "{{ page.title }}",
        "directory": "{{ page.title }}",
        "gallery": "{{ page.title }}",
        "image": "{{ page.title }}",
    }
    defaults.update(templates)
    for name, content in defaults.items():
        (theme / f"{name}.html").write_text(content)
    return theme


def _make_home(tmp_path, index_text=None):
    """Create a HOME node rooted at tmp_path with optional index.md."""
    root = Node(str(tmp_path), type="HOME")
    if index_text is not None:
        index = tmp_path / "index.md"
        index.write_text(index_text)
        root.index_path = str(index)
    return root


# --- __init__ ---


def test_init_creates_jinja_env(tmp_path):
    theme = _make_theme(tmp_path)
    config = Config(cli_args={"theme_path": str(theme)})
    r = Builder(config)
    assert r.env is not None
    tmpl = r.env.get_template("default.html")
    assert tmpl is not None


def test_init_uses_bundled_theme_by_default():
    config = Config()
    r = Builder(config)
    tmpl = r.env.get_template("default.html")
    assert tmpl is not None


# --- _get_output_path ---


def test_output_path_home(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    assert r._get_output_path(root, tmp_path) == "index.html"


def test_output_path_markdown(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    page_file = tmp_path / "about.md"
    page_file.write_text("# About")
    page = Node(str(page_file), parent=root, type="PAGE")
    assert r._get_output_path(page, tmp_path) == "about/index.html"


def test_output_path_directory(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    dir_node = Node(str(sub), parent=root, type="DIRECTORY")
    assert r._get_output_path(dir_node, tmp_path) == "blog/index.html"


def test_output_path_gallery(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "photos"
    sub.mkdir()
    gal_node = Node(str(sub), parent=root, type="GALLERY")
    assert r._get_output_path(gal_node, tmp_path) == "photos/index.html"


def test_output_path_nested_directory(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    deep = sub / "2024"
    deep.mkdir()
    dir_node = Node(str(sub), parent=root, type="DIRECTORY")
    deep_node = Node(str(deep), parent=dir_node, type="DIRECTORY")
    assert r._get_output_path(deep_node, tmp_path) == "blog/2024/index.html"


def test_output_path_nested_markdown(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    page_file = sub / "post.md"
    page_file.write_text("# Post")
    dir_node = Node(str(sub), parent=root, type="DIRECTORY")
    page = Node(str(page_file), parent=dir_node, type="PAGE")
    assert r._get_output_path(page, tmp_path) == "blog/post/index.html"


# --- template_name ---


def test_template_name_home():
    node = Node.__new__(Node)
    node.type = "HOME"
    node.index_path = "/some/index.md"
    assert node.template_name == "home.html"


def test_template_name_markdown():
    node = Node.__new__(Node)
    node.type = "PAGE"
    assert node.template_name == "page.html"


def test_template_name_page_bundle():
    node = Node.__new__(Node)
    node.type = "PAGE"
    node.index_path = "/some/index.md"
    assert node.template_name == "page.html"


def test_template_name_directory_without_index():
    node = Node.__new__(Node)
    node.type = "DIRECTORY"
    node.index_path = None
    assert node.template_name == "directory.html"


def test_template_name_gallery():
    node = Node.__new__(Node)
    node.type = "GALLERY"
    assert node.template_name == "gallery.html"


# --- _build_page_context ---


def _init_shortcodes(builder, source_path):
    """Set up shortcode processing so _build_page_context can be called directly."""
    builder._source_path = source_path
    index = SuffixIndex(source_path)
    builder._shortcodes = ShortcodeProcessor(index, builder.env, builder._resolve_url)


def test_page_context_from_markdown(tmp_path):
    config = Config()
    r = Builder(config)
    _init_shortcodes(r, str(tmp_path))
    md_file = tmp_path / "page.md"
    md_file.write_text("# My Title\n\nSome content.")
    node = Node(str(md_file), type="PAGE")
    ctx = r._build_page_context(node)
    assert ctx["title"] == "My Title"
    assert "Some content." in ctx["content"]
    assert "<h1>" not in ctx["content"]


def test_page_context_title_fallback(tmp_path):
    config = Config()
    r = Builder(config)
    _init_shortcodes(r, str(tmp_path))
    md_file = tmp_path / "page.md"
    md_file.write_text("No heading here, just text.")
    node = Node(str(md_file), type="PAGE")
    ctx = r._build_page_context(node)
    assert ctx["title"] == "page"


def test_page_context_directory_no_markdown(tmp_path):
    config = Config()
    r = Builder(config)
    sub = tmp_path / "photos"
    sub.mkdir()
    node = Node(str(sub), type="GALLERY")
    node.index_path = None
    img = Node.__new__(Node)
    img.type = "IMAGE"
    img.name = "a.jpg"
    img.stem = "a"
    img.path = str(sub / "a.jpg")
    img._metadata = None
    node.images = [img]
    node.pages = []
    node.dirs = []
    ctx = r._build_page_context(node)
    assert ctx["title"] == "photos"
    assert ctx["content"] == ""
    assert len(ctx["images"]) == 1
    assert ctx["images"][0].name == "a.jpg"
    assert ctx["images"][0].url == "a/"
    assert ctx["images"][0].src == "a/a.jpg"


def test_page_context_directory_with_children(tmp_path):
    config = Config()
    r = Builder(config)
    sub = tmp_path / "blog"
    sub.mkdir()
    node = Node(str(sub), type="DIRECTORY")
    node.index_path = None

    page = Node.__new__(Node)
    page.type = "PAGE"
    page.name = "post.md"
    page.stem = "post"
    page.path = str(sub / "post.md")
    node.pages = [page]

    child_dir = Node.__new__(Node)
    child_dir.type = "DIRECTORY"
    child_dir.name = "archive"
    child_dir.path = str(sub / "archive")
    node.dirs = [child_dir]
    node.images = []

    ctx = r._build_page_context(node)
    assert len(ctx["pages"]) == 1
    assert ctx["pages"][0]["name"] == "post"
    assert ctx["pages"][0]["url"] == "post/"
    assert len(ctx["dirs"]) == 1
    assert ctx["dirs"][0]["name"] == "archive"
    assert ctx["dirs"][0]["url"] == "archive/"


# --- _copy_theme_assets ---


def test_copy_theme_assets(tmp_path):
    theme = _make_theme(tmp_path)
    static = theme / "static"
    static.mkdir()
    (static / "styles.css").write_text("body {}")
    (static / "script.js").write_text("console.log()")
    public = tmp_path / "public"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})
    r = Builder(config)
    public.mkdir()
    r._copy_theme_assets()
    assert (public / "styles.css").exists()
    assert (public / "script.js").exists()
    # templates should NOT be copied
    assert not (public / "default.html").exists()


def test_copy_theme_assets_recursive(tmp_path):
    theme = _make_theme(tmp_path)
    static = theme / "static"
    static.mkdir()
    css_dir = static / "css"
    css_dir.mkdir()
    (css_dir / "main.css").write_text("body {}")
    js_dir = static / "js"
    js_dir.mkdir()
    (js_dir / "app.js").write_text("console.log()")
    public = tmp_path / "public"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})
    r = Builder(config)
    public.mkdir()
    r._copy_theme_assets()
    assert (public / "css" / "main.css").exists()
    assert (public / "js" / "app.js").exists()


def test_copy_theme_assets_no_static_dir(tmp_path):
    theme = _make_theme(tmp_path)
    public = tmp_path / "public"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})
    r = Builder(config)
    public.mkdir()
    r._copy_theme_assets()
    # Only the public dir itself should exist, with no files copied
    assert list(public.iterdir()) == []


def test_copy_bundled_theme_assets(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    assert (public / "styles.css").exists()
    # templates should NOT be copied
    assert not (public / "default.html").exists()


# --- render (integration) ---


def test_render_basic_site(tmp_path):
    # Set up source
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Welcome\n\nHello world.")

    # Set up theme
    theme = _make_theme(
        tmp_path,
        home="<title>{{ page.title }}</title><main>{{ page.content }}</main>",
    )
    static = theme / "static"
    static.mkdir()
    (static / "styles.css").write_text("body {}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    index = public / "index.html"
    assert index.exists()
    html = index.read_text()
    assert "<title>Welcome</title>" in html
    assert "Hello world." in html
    # theme assets copied
    assert (public / "styles.css").exists()


def test_render_markdown_page(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "about.md").write_text("# About Us\n\nWe are cool.")

    theme = _make_theme(
        tmp_path,
        home="<title>{{ page.title }}</title>{{ page.content }}",
        page="<title>{{ page.title }}</title>{{ page.content }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    out = public / "about" / "index.html"
    assert out.exists()
    html = out.read_text()
    assert "<title>About Us</title>" in html
    assert "We are cool." in html


def test_render_nested_markdown_page(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    blog = source / "blog"
    blog.mkdir()
    (blog / "post.md").write_text("# My Post\n\nPost content.")

    theme = _make_theme(
        tmp_path,
        page="<title>{{ page.title }}</title>{{ page.content }}",
        directory="<h1>{{ page.title }}</h1>",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    out = public / "blog" / "post" / "index.html"
    assert out.exists()
    html = out.read_text()
    assert "<title>My Post</title>" in html
    assert "Post content." in html


def test_render_copies_images(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    theme = _make_theme(
        tmp_path,
        gallery="{% for img in page.images %}{{ img.src }}{% endfor %}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    # Image now lives in its pretty URL directory
    assert (public / "photos" / "a" / "a.jpg").exists()
    assert (public / "photos" / "a" / "index.html").exists()
    assert (public / "photos" / "index.html").exists()


def test_render_copies_static_assets(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.json").write_text('{"key": "value"}')

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    assert (public / "data.json").exists()


def test_render_directory_listing(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    sub = source / "docs"
    sub.mkdir()
    (sub / "page.md").write_text("# A Page")

    theme = _make_theme(
        tmp_path,
        directory=(
            "<h1>{{ page.title }}</h1>"
            '{% for p in page.pages %}<a href="{{ p.url }}">{{ p.name }}</a>{% endfor %}'
        ),
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    dir_html = (public / "docs" / "index.html").read_text()
    assert "<h1>docs</h1>" in dir_html
    assert "page" in dir_html


def test_render_site_context(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    theme = _make_theme(
        tmp_path,
        home="{{ site.title }} - {{ site.language }}",
    )

    public = tmp_path / "output"
    config = Config(
        cli_args={
            "theme_path": str(theme),
            "public_path": str(public),
            "site.title": "Test Site",
        }
    )

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert "Test Site" in html
    assert "en-us" in html


def test_render_generator_context(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    theme = _make_theme(
        tmp_path,
        home="{{ generator.name }} {{ generator.package }} {{ generator.version }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert "Static Gallery" in html
    assert "static-gallery" in html
    assert "0.1.0" in html


def test_bundled_theme_has_generator_meta(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert '<meta name="generator"' in html
    assert "Static Gallery" in html


def test_bundled_theme_has_viewport_meta(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert '<meta name="viewport"' in html


def test_bundled_theme_uses_mdash_not_emdash(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert "&mdash;" in html
    assert "&emdash;" not in html


def test_bundled_gallery_uses_alt_text(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    gallery_node = site.root.dirs[0]
    gallery_node.images[0]._metadata = make_metadata(alt_text="A sunset photo")

    Builder(config).render(site)

    # Gallery page thumbnail
    gallery_html = (public / "photos" / "index.html").read_text()
    assert 'alt="A sunset photo"' in gallery_html

    # Image page
    img_html = (public / "photos" / "a" / "index.html").read_text()
    assert 'alt="A sunset photo"' in img_html


def test_bundled_gallery_alt_falls_back_to_name(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    gallery_node = site.root.dirs[0]
    gallery_node.images[0]._metadata = Metadata()

    Builder(config).render(site)

    html = (public / "photos" / "index.html").read_text()
    assert 'alt="a.jpg"' in html


def test_bundled_gallery_no_figcaption_without_metadata(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    gallery_node = site.root.dirs[0]
    gallery_node.images[0]._metadata = Metadata()

    Builder(config).render(site)

    # Gallery page should not have figcaption
    gallery_html = (public / "photos" / "index.html").read_text()
    assert "<figcaption>" not in gallery_html


# --- collision detection ---


def test_markdown_directory_collision(tmp_path):
    """blog.md + blog/index.md both map to blog/index.html — should error."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "blog.md").write_text("# Blog page")
    blog = source / "blog"
    blog.mkdir()
    (blog / "index.md").write_text("# Blog index")

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))

    with pytest.raises(RuntimeError, match="blog/index.html"):
        Builder(config).render(site)


def test_markdown_directory_static_collision(tmp_path):
    """archive.md + archive/index.html both map to archive/index.html."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "archive.md").write_text("# Archive page")
    archive = source / "archive"
    archive.mkdir()
    (archive / "index.html").write_text("<h1>Static archive</h1>")

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))

    with pytest.raises(RuntimeError, match="archive/index.html"):
        Builder(config).render(site)


def test_no_collision_normal_site(tmp_path):
    """A typical site with no conflicts should build without error."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Home")
    (source / "about.md").write_text("# About")
    blog = source / "blog"
    blog.mkdir()
    (blog / "post.md").write_text("# Post")

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    assert (public / "index.html").exists()
    assert (public / "about" / "index.html").exists()
    assert (public / "blog" / "post" / "index.html").exists()


def test_html_page_directory_collision(tmp_path):
    """about.html + about/index.md both map to about/index.html — should error."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "about.html").write_text("<h1>About page</h1>")
    about = source / "about"
    about.mkdir()
    (about / "index.md").write_text("# About bundle")

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))

    with pytest.raises(RuntimeError, match="about/index.html"):
        Builder(config).render(site)


def test_render_page_bundle_with_children(tmp_path):
    """Page bundle renders its own page and all children correctly."""
    source = tmp_path / "source"
    source.mkdir()
    about = source / "about"
    about.mkdir()
    (about / "index.md").write_text("# About Us\n\nWe are cool.")
    (about / "photo.jpg").write_bytes(b"\xff\xd8\xff")
    (about / "data.json").write_text('{"key": "value"}')

    theme = _make_theme(
        tmp_path,
        page="<title>{{ page.title }}</title>{{ page.content }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    # Page bundle index rendered
    about_html = (public / "about" / "index.html").read_text()
    assert "<title>About Us</title>" in about_html
    assert "We are cool." in about_html

    # Image child rendered with its own page and file copied
    assert (public / "about" / "photo" / "index.html").exists()
    assert (public / "about" / "photo" / "photo.jpg").exists()

    # Static asset copied
    assert (public / "about" / "data.json").exists()


def test_output_path_image(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    img_file = tmp_path / "photo.jpg"
    img_file.write_bytes(b"\xff\xd8\xff")
    img = Node(str(img_file), parent=root, type="IMAGE")
    assert r._get_output_path(img, tmp_path) == "photo/index.html"


def test_output_path_nested_image(tmp_path):
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "photos"
    sub.mkdir()
    img_file = sub / "sunset.jpg"
    img_file.write_bytes(b"\xff\xd8\xff")
    dir_node = Node(str(sub), parent=root, type="GALLERY")
    img = Node(str(img_file), parent=dir_node, type="IMAGE")
    assert r._get_output_path(img, tmp_path) == "photos/sunset/index.html"


def test_image_file_output_path(tmp_path):
    config = Config()
    r = Builder(config)
    img_file = tmp_path / "photo.jpg"
    img_file.write_bytes(b"\xff\xd8\xff")
    img = Node(str(img_file), parent=None, type="IMAGE")
    assert r._get_image_file_output_path(img, tmp_path) == "photo/photo.jpg"


def test_render_image_page(tmp_path):
    """Each image gets its own HTML page at stem/index.html."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    theme = _make_theme(
        tmp_path,
        gallery='{% for img in page.images %}<a href="{{ img.url }}"><img src="{{ img.src }}"></a>{% endfor %}',
        image='<title>{{ page.title }}</title><img src="{{ page.image.url }}">',
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    # Image page exists
    assert (public / "photos" / "a" / "index.html").exists()
    img_html = (public / "photos" / "a" / "index.html").read_text()
    assert "<title>a</title>" in img_html
    assert 'src="a.jpg"' in img_html

    # Image file relocated to pretty URL dir
    assert (public / "photos" / "a" / "a.jpg").exists()

    # Gallery page links correctly
    gallery_html = (public / "photos" / "index.html").read_text()
    assert 'href="a/"' in gallery_html
    assert 'src="a/a.jpg"' in gallery_html


def test_render_image_page_with_paired_markdown(tmp_path):
    """Paired markdown provides title and content for image page."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "sunset.jpg").write_bytes(b"\xff\xd8\xff")
    (photos / "sunset.md").write_text("# Golden Sunset\n\nTaken at the beach.")

    theme = _make_theme(
        tmp_path,
        image="<title>{{ page.title }}</title>{{ page.content }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    img_html = (public / "photos" / "sunset" / "index.html").read_text()
    assert "<title>Golden Sunset</title>" in img_html
    assert "Taken at the beach." in img_html


def test_render_image_page_with_metadata(tmp_path):
    """Image metadata is available in image page context."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")

    theme = _make_theme(
        tmp_path,
        image="{{ page.image.camera }} {{ page.image.name }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    site.root.dirs[0].images[0]._metadata = make_metadata(camera="Nikon Z6")

    Builder(config).render(site)

    img_html = (public / "photos" / "a" / "index.html").read_text()
    assert "Nikon Z6" in img_html
    assert "a.jpg" in img_html


def test_page_context_images_have_url_and_src(tmp_path):
    """Parent nodes list images with url (page link) and src (file path)."""
    config = Config()
    r = Builder(config)
    sub = tmp_path / "photos"
    sub.mkdir()
    node = Node(str(sub), type="GALLERY")
    node.index_path = None

    img = Node.__new__(Node)
    img.type = "IMAGE"
    img.name = "a.jpg"
    img.stem = "a"
    img.path = str(sub / "a.jpg")
    img._metadata = None
    node.images = [img]
    node.pages = []
    node.dirs = []

    ctx = r._build_page_context(node)
    assert ctx["images"][0].url == "a/"
    assert ctx["images"][0].src == "a/a.jpg"


def test_gallery_context_images_sorted_by_datetime(tmp_path):
    """Gallery page context lists images in chronological order."""
    config = Config()
    r = Builder(config)
    sub = tmp_path / "photos"
    sub.mkdir()
    node = Node(str(sub), type="GALLERY")
    node.index_path = None

    def _img(name, dt_str):
        img = Node.__new__(Node)
        img.type = "IMAGE"
        img.name = name
        img.stem = name.split(".")[0]
        img.path = str(sub / name)
        img._metadata = make_metadata(datetime=dt_str)
        return img

    img_c = _img("c.jpg", "2024:01:03 00:00:00")
    img_a = _img("a.jpg", "2024:01:01 00:00:00")
    img_b = _img("b.jpg", "2024:01:02 00:00:00")
    node.images = [img_c, img_a, img_b]
    node.pages = []
    node.dirs = []

    ctx = r._build_page_context(node)
    names = [img.name for img in ctx["images"]]
    assert names == ["a.jpg", "b.jpg", "c.jpg"]


def test_image_stem_directory_collision(tmp_path):
    """sunset.jpg + sunset/ directory should collide on sunset/index.html."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "sunset.jpg").write_bytes(b"\xff\xd8\xff")
    sunset_dir = source / "sunset"
    sunset_dir.mkdir()
    (sunset_dir / "page.md").write_text("# Sunset page")

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))

    with pytest.raises(RuntimeError, match="sunset/index.html"):
        Builder(config).render(site)


def test_render_public_defaults_to_public_dir(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    theme = _make_theme(tmp_path, home="ok")

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        config = Config(cli_args={"theme_path": str(theme)})
        site = Scanner(config).scan(str(source))
        Builder(config).render(site)
        assert (tmp_path / "public" / "index.html").exists()
    finally:
        os.chdir(old_cwd)


# --- shortcode integration ---


def test_render_embed_image_shortcode(tmp_path):
    """Embed shortcode in markdown renders as <img> in output HTML."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "sunset.jpg").write_bytes(b"\xff\xd8\xff")
    (source / "index.md").write_text("# Home\n\n<</photos/sunset.jpg>>")

    theme = _make_theme(tmp_path, home="{{ page.content }}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert "<img" in html
    assert "sunset.jpg" in html


def test_render_embed_code_shortcode(tmp_path):
    """Embed shortcode for code file renders as <pre><code> in output."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "hello.py").write_text('print("hi")')
    (source / "index.md").write_text("# Home\n\n<</hello.py>>")

    theme = _make_theme(tmp_path, home="{{ page.content }}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert '<pre><code class="language-py">' in html
    assert "print" in html


def test_render_gallery_shortcode(tmp_path):
    """Gallery shortcode in index.md renders gallery HTML."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (photos / "index.md").write_text("# Photos\n\n<<gallery>>")

    public = tmp_path / "output"
    config = Config(cli_args={"public_path": str(public)})

    site = Scanner(config).scan(str(source))
    site.root.pages[0].images[0]._metadata = Metadata()
    Builder(config).render(site)

    html = (public / "photos" / "index.html").read_text()
    assert 'class="gallery"' in html
    assert "a/a.jpg" in html


def test_render_link_embed_static_file(tmp_path):
    """Link embed of a static file produces correct <a href> URL."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.csv").write_text("a,b,c")
    (source / "index.md").write_text("# Home\n\n<</data.csv>>")

    theme = _make_theme(tmp_path, home="{{ page.content }}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert '<a href="data.csv">' in html


def test_render_cross_directory_embed(tmp_path):
    """Shortcode in blog/post.md referencing photos/sunset.jpg produces correct relative path."""
    source = tmp_path / "source"
    source.mkdir()
    blog = source / "blog"
    blog.mkdir()
    (blog / "post.md").write_text("# Post\n\n<</photos/sunset.jpg>>")
    photos = source / "photos"
    photos.mkdir()
    (photos / "sunset.jpg").write_bytes(b"\xff\xd8\xff")

    theme = _make_theme(tmp_path, page="{{ page.content }}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "blog" / "post" / "index.html").read_text()
    assert "<img" in html
    # Should be a relative path from blog/post/ to photos/sunset/sunset.jpg
    assert "photos/sunset/sunset.jpg" in html


def test_render_shortcodes_in_paired_markdown(tmp_path):
    """IMAGE node with content_path containing shortcodes renders them."""
    source = tmp_path / "source"
    source.mkdir()
    photos = source / "photos"
    photos.mkdir()
    (photos / "sunset.jpg").write_bytes(b"\xff\xd8\xff")
    (photos / "sunset.md").write_text("# Sunset\n\n<</photos/sunset.jpg>>")

    theme = _make_theme(
        tmp_path,
        image="<title>{{ page.title }}</title>{{ page.content }}",
    )

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    site.root.dirs[0].images[0]._metadata = Metadata()
    Builder(config).render(site)

    html = (public / "photos" / "sunset" / "index.html").read_text()
    assert "<title>Sunset</title>" in html
    assert "<img" in html
    assert "sunset.jpg" in html


def test_render_html_page_copied_raw(tmp_path):
    """HTML PAGE nodes are copied to pretty URL path without template wrapping."""
    source = tmp_path / "source"
    source.mkdir()
    html_content = "<html><body><h1>About</h1></body></html>"
    (source / "about.html").write_text(html_content)

    theme = _make_theme(tmp_path)

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    out = public / "about" / "index.html"
    assert out.exists()
    assert out.read_text() == html_content


def test_render_html_index_in_page_bundle(tmp_path):
    """Page bundle with index.html inserts raw HTML content into template."""
    source = tmp_path / "source"
    source.mkdir()
    about = source / "about"
    about.mkdir()
    (about / "index.html").write_text("<p>About us content</p>")

    theme = _make_theme(tmp_path, page="<main>{{ page.content }}</main>")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "about" / "index.html").read_text()
    assert "<main><p>About us content</p></main>" in html


def test_output_path_html_page(tmp_path):
    """HTML PAGE nodes get pretty URLs like markdown pages."""
    config = Config()
    r = Builder(config)
    root = _make_home(tmp_path)
    page_file = tmp_path / "about.html"
    page_file.write_text("<h1>About</h1>")
    page = Node(str(page_file), parent=root, type="PAGE")
    assert r._get_output_path(page, tmp_path) == "about/index.html"


def test_render_no_shortcodes_unchanged(tmp_path):
    """Markdown without shortcodes renders normally."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hello\n\nNo shortcodes here.")

    theme = _make_theme(tmp_path, home="{{ page.content }}")

    public = tmp_path / "output"
    config = Config(cli_args={"theme_path": str(theme), "public_path": str(public)})

    site = Scanner(config).scan(str(source))
    Builder(config).render(site)

    html = (public / "index.html").read_text()
    assert "No shortcodes here." in html
    assert "<<" not in html
