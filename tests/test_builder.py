import os

from static_gallery.config import StaticGalleryConfig
from static_gallery.nodes import StaticGalleryNode
from static_gallery.builder import StaticGalleryBuilder


def _make_home(tmp_path, index_text=None):
    """Create a HOME node rooted at tmp_path with optional index.md."""
    root = StaticGalleryNode(str(tmp_path), type="HOME")
    if index_text is not None:
        index = tmp_path / "index.md"
        index.write_text(index_text)
        root.text = str(index)
    return root


# --- __init__ ---


def test_init_creates_jinja_env(tmp_path):
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")
    config = StaticGalleryConfig(cli_args={"theme_path": str(theme)})
    r = StaticGalleryBuilder(config)
    assert r.env is not None
    tmpl = r.env.get_template("_default.html")
    assert tmpl is not None


def test_init_uses_bundled_theme_by_default():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    tmpl = r.env.get_template("_default.html")
    assert tmpl is not None


# --- _get_output_path ---


def test_output_path_home(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    assert r._get_output_path(root, tmp_path) == "index.html"


def test_output_path_markdown(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    page_file = tmp_path / "about.md"
    page_file.write_text("# About")
    page = StaticGalleryNode(str(page_file), parent=root, type="MARKDOWN")
    assert r._get_output_path(page, tmp_path) == "about/index.html"


def test_output_path_directory(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    dir_node = StaticGalleryNode(str(sub), parent=root, type="DIRECTORY")
    assert r._get_output_path(dir_node, tmp_path) == "blog/index.html"


def test_output_path_gallery(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "photos"
    sub.mkdir()
    gal_node = StaticGalleryNode(str(sub), parent=root, type="GALLERY")
    assert r._get_output_path(gal_node, tmp_path) == "photos/index.html"


def test_output_path_nested_directory(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    deep = sub / "2024"
    deep.mkdir()
    dir_node = StaticGalleryNode(str(sub), parent=root, type="DIRECTORY")
    deep_node = StaticGalleryNode(str(deep), parent=dir_node, type="DIRECTORY")
    assert r._get_output_path(deep_node, tmp_path) == "blog/2024/index.html"


def test_output_path_nested_markdown(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    root = _make_home(tmp_path)
    sub = tmp_path / "blog"
    sub.mkdir()
    page_file = sub / "post.md"
    page_file.write_text("# Post")
    dir_node = StaticGalleryNode(str(sub), parent=root, type="DIRECTORY")
    page = StaticGalleryNode(str(page_file), parent=dir_node, type="MARKDOWN")
    assert r._get_output_path(page, tmp_path) == "blog/post/index.html"


# --- _get_template_name ---


def test_template_name_home():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    node = StaticGalleryNode.__new__(StaticGalleryNode)
    node.type = "HOME"
    node.text = "/some/index.md"
    assert r._get_template_name(node) == "_default.html"


def test_template_name_markdown():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    node = StaticGalleryNode.__new__(StaticGalleryNode)
    node.type = "MARKDOWN"
    assert r._get_template_name(node) == "_default.html"


def test_template_name_directory_with_index():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    node = StaticGalleryNode.__new__(StaticGalleryNode)
    node.type = "DIRECTORY"
    node.text = "/some/index.md"
    assert r._get_template_name(node) == "_default.html"


def test_template_name_directory_without_index():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    node = StaticGalleryNode.__new__(StaticGalleryNode)
    node.type = "DIRECTORY"
    node.text = None
    assert r._get_template_name(node) == "_directory.html"


def test_template_name_gallery():
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    node = StaticGalleryNode.__new__(StaticGalleryNode)
    node.type = "GALLERY"
    assert r._get_template_name(node) == "_gallery.html"


# --- _build_page_context ---


def test_page_context_from_markdown(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    md_file = tmp_path / "page.md"
    md_file.write_text("# My Title\n\nSome content.")
    node = StaticGalleryNode(str(md_file), type="MARKDOWN")
    ctx = r._build_page_context(node)
    assert ctx["title"] == "My Title"
    assert "Some content." in ctx["content"]
    assert "<h1>" not in ctx["content"]


def test_page_context_title_fallback(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    md_file = tmp_path / "page.md"
    md_file.write_text("No heading here, just text.")
    node = StaticGalleryNode(str(md_file), type="MARKDOWN")
    ctx = r._build_page_context(node)
    assert ctx["title"] == "page"


def test_page_context_directory_no_markdown(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    sub = tmp_path / "photos"
    sub.mkdir()
    node = StaticGalleryNode(str(sub), type="GALLERY")
    node.text = None
    img = StaticGalleryNode.__new__(StaticGalleryNode)
    img.type = "IMAGE"
    img.name = "a.jpg"
    img.path = str(sub / "a.jpg")
    node.images = [img]
    node.pages = []
    node.dirs = []
    ctx = r._build_page_context(node)
    assert ctx["title"] == "photos"
    assert ctx["content"] == ""
    assert len(ctx["images"]) == 1
    assert ctx["images"][0]["name"] == "a.jpg"
    assert ctx["images"][0]["url"] == "a.jpg"


def test_page_context_directory_with_children(tmp_path):
    config = StaticGalleryConfig()
    r = StaticGalleryBuilder(config)
    sub = tmp_path / "blog"
    sub.mkdir()
    node = StaticGalleryNode(str(sub), type="DIRECTORY")
    node.text = None

    page = StaticGalleryNode.__new__(StaticGalleryNode)
    page.type = "MARKDOWN"
    page.name = "post.md"
    page.stem = "post"
    page.path = str(sub / "post.md")
    node.pages = [page]

    child_dir = StaticGalleryNode.__new__(StaticGalleryNode)
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
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")
    (theme / "styles.css").write_text("body {}")
    (theme / "script.js").write_text("console.log()")
    public = tmp_path / "public"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )
    r = StaticGalleryBuilder(config)
    public.mkdir()
    r._copy_theme_assets()
    assert (public / "styles.css").exists()
    assert (public / "script.js").exists()
    # underscore-prefixed templates should NOT be copied
    assert not (public / "_default.html").exists()


def test_copy_theme_assets_recursive(tmp_path):
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")
    css_dir = theme / "css"
    css_dir.mkdir()
    (css_dir / "main.css").write_text("body {}")
    js_dir = theme / "js"
    js_dir.mkdir()
    (js_dir / "app.js").write_text("console.log()")
    public = tmp_path / "public"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )
    r = StaticGalleryBuilder(config)
    public.mkdir()
    r._copy_theme_assets()
    assert (public / "css" / "main.css").exists()
    assert (public / "js" / "app.js").exists()


# --- render (integration) ---


def test_render_basic_site(tmp_path):
    # Set up source
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Welcome\n\nHello world.")

    # Set up theme
    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text(
        "<title>{{ page.title }}</title><main>{{ page.content }}</main>"
    )
    (theme / "styles.css").write_text("body {}")

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

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

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text(
        "<title>{{ page.title }}</title>{{ page.content }}"
    )

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

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

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text(
        "<title>{{ page.title }}</title>{{ page.content }}"
    )
    (theme / "_directory.html").write_text("<h1>{{ page.title }}</h1>")

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

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

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")
    (theme / "_gallery.html").write_text(
        "{% for img in page.images %}{{ img.url }}{% endfor %}"
    )

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

    assert (public / "photos" / "a.jpg").exists()
    assert (public / "photos" / "index.html").exists()


def test_render_copies_static_assets(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.json").write_text('{"key": "value"}')

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

    assert (public / "data.json").exists()


def test_render_directory_listing(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    sub = source / "docs"
    sub.mkdir()
    (sub / "page.md").write_text("# A Page")

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ page.title }}")
    (theme / "_directory.html").write_text(
        "<h1>{{ page.title }}</h1>"
        '{% for p in page.pages %}<a href="{{ p.url }}">{{ p.name }}</a>{% endfor %}'
    )

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={"theme_path": str(theme), "public_path": str(public)}
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

    dir_html = (public / "docs" / "index.html").read_text()
    assert "<h1>docs</h1>" in dir_html
    assert "page" in dir_html


def test_render_site_context(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("{{ site.title }} - {{ site.language }}")

    public = tmp_path / "output"
    config = StaticGalleryConfig(
        cli_args={
            "theme_path": str(theme),
            "public_path": str(public),
            "site.title": "Test Site",
        }
    )

    from static_gallery.scanner import Scanner

    root = Scanner(config).scan(str(source))
    StaticGalleryBuilder(config).render(root, str(source))

    html = (public / "index.html").read_text()
    assert "Test Site" in html
    assert "en-us" in html


def test_render_public_defaults_to_public_dir(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.md").write_text("# Hi")

    theme = tmp_path / "theme"
    theme.mkdir()
    (theme / "_default.html").write_text("ok")

    config = StaticGalleryConfig(cli_args={"theme_path": str(theme)})

    from static_gallery.scanner import Scanner

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        root = Scanner(config).scan(str(source))
        StaticGalleryBuilder(config).render(root, str(source))
        assert (tmp_path / "public" / "index.html").exists()
    finally:
        os.chdir(old_cwd)
