import os

from jinja2 import DictLoader, Environment

from static_gallery.node import Node, NodeType
from static_gallery.shortcodes import ShortcodeProcessor


def _make_env(templates=None):
    if templates is None:
        templates = {
            "codes/gallery.html": (
                '<div class="gallery">'
                "{% for img in images %}"
                '<img src="{{ img.src }}">'
                "{% endfor %}"
                "</div>"
            )
        }
    return Environment(loader=DictLoader(templates), autoescape=True)


def _make_node(path, type, name=None, stem=None, suffix="", metadata=None):
    node = Node.__new__(Node)
    node.path = path
    node.type = type
    node.name = name or os.path.basename(path)
    node.stem = stem or os.path.splitext(node.name)[0]
    node.suffix = suffix
    node._metadata = metadata
    node.images = []
    node.pages = []
    node.assets = []
    node.dirs = []
    node.index_path = None
    node.content_path = None
    return node


def _make_processor(root, source_path="/src", env=None):
    if env is None:
        env = _make_env()

    def resolve_url(current, target, image_file=False):
        if target.type == NodeType.IMAGE and image_file:
            return target.stem + "/" + target.name
        if target.type == NodeType.IMAGE:
            return target.stem + "/"
        return target.name

    return ShortcodeProcessor(root, source_path, env, resolve_url)


# --- Parsing ---


def test_no_shortcodes():
    root = _make_node("/src", NodeType.HOME)
    p = _make_processor(root)
    text = "Hello world, no shortcodes here."
    assert p.process(text, root) == text


def test_embed_shortcode_detected():
    root = _make_node("/src", NodeType.HOME)
    img = _make_node("/src/photo.jpg", NodeType.IMAGE, suffix=".jpg")
    root.images = [img]
    p = _make_processor(root)
    result = p.process("Look: <</photo.jpg>>", root)
    assert "<img" in result
    assert "photo.jpg" in result


def test_multiple_shortcodes():
    root = _make_node("/src", NodeType.HOME)
    img1 = _make_node("/src/a.jpg", NodeType.IMAGE, suffix=".jpg")
    img2 = _make_node("/src/b.jpg", NodeType.IMAGE, suffix=".jpg")
    root.images = [img1, img2]
    p = _make_processor(root)
    result = p.process("First: <</a.jpg>> Second: <</b.jpg>>", root)
    assert result.count("<img") == 2


def test_embed_with_leading_slash_stripped():
    root = _make_node("/src", NodeType.HOME)
    img = _make_node("/src/photo.jpg", NodeType.IMAGE, suffix=".jpg")
    root.images = [img]
    p = _make_processor(root)
    result = p.process("<</photo.jpg>>", root)
    assert "<img" in result


# --- Embed: Images ---


def test_embed_image_produces_img_tag():
    root = _make_node("/src", NodeType.HOME)
    img = _make_node("/src/sunset.jpg", NodeType.IMAGE, suffix=".jpg")
    root.images = [img]
    p = _make_processor(root)
    result = p.process("<</sunset.jpg>>", root)
    assert 'src="sunset/sunset.jpg"' in result
    assert 'alt="sunset.jpg"' in result


def test_embed_nested_image():
    root = _make_node("/src", NodeType.HOME)
    photos = _make_node("/src/photos", NodeType.GALLERY)
    img = _make_node("/src/photos/castle.jpg", NodeType.IMAGE, suffix=".jpg")
    photos.images = [img]
    root.dirs = [photos]
    p = _make_processor(root)
    result = p.process("<</photos/castle.jpg>>", root)
    assert "<img" in result
    assert "castle.jpg" in result


def test_embed_not_found_returns_escaped():
    root = _make_node("/src", NodeType.HOME)
    p = _make_processor(root)
    result = p.process("<</missing.jpg>>", root)
    assert "&lt;&lt;/missing.jpg&gt;&gt;" in result


# --- Embed: Code files ---


def test_embed_code_file(tmp_path):
    py_file = tmp_path / "hello.py"
    py_file.write_text('print("hello")')
    root = _make_node(str(tmp_path), NodeType.HOME)
    asset = _make_node(str(py_file), NodeType.STATIC, suffix=".py")
    root.assets = [asset]
    p = _make_processor(root, source_path=str(tmp_path))
    result = p.process("<</hello.py>>", root)
    assert '<pre><code class="language-py">' in result
    assert "print(&quot;hello&quot;)" in result


def test_embed_code_escapes_html(tmp_path):
    js_file = tmp_path / "app.js"
    js_file.write_text('const x = "<div>"')
    root = _make_node(str(tmp_path), NodeType.HOME)
    asset = _make_node(str(js_file), NodeType.STATIC, suffix=".js")
    root.assets = [asset]
    p = _make_processor(root, source_path=str(tmp_path))
    result = p.process("<</app.js>>", root)
    assert "&lt;div&gt;" in result


# --- Embed: Other files ---


def test_embed_unknown_file_produces_link(tmp_path):
    dat_file = tmp_path / "data.csv"
    dat_file.write_text("a,b,c")
    root = _make_node(str(tmp_path), NodeType.HOME)
    asset = _make_node(str(dat_file), NodeType.STATIC, suffix=".csv")
    root.assets = [asset]
    p = _make_processor(root, source_path=str(tmp_path))
    result = p.process("<</data.csv>>", root)
    assert "<a " in result
    assert "data.csv" in result


# --- Gallery shortcode ---


def test_gallery_shortcode_renders():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    img = _make_node("/src/photos/a.jpg", NodeType.IMAGE, suffix=".jpg", metadata={})
    gallery.images = [img]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process("<<gallery>>", gallery)
    assert '<div class="gallery">' in result
    assert "a/a.jpg" in result


def test_gallery_shortcode_filter():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    jpg = _make_node("/src/photos/a.jpg", NodeType.IMAGE, suffix=".jpg", metadata={})
    png = _make_node("/src/photos/b.png", NodeType.IMAGE, suffix=".png", metadata={})
    gallery.images = [jpg, png]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process('<<gallery filter="*.jpg">>', gallery)
    assert "a/a.jpg" in result
    assert "b/b.png" not in result


def test_gallery_shortcode_sort():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    img_a = _make_node(
        "/src/photos/a.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={"datetime": "2024-01-02"},
    )
    img_b = _make_node(
        "/src/photos/b.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={"datetime": "2024-01-01"},
    )
    gallery.images = [img_a, img_b]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process('<<gallery sort="datetime">>', gallery)
    pos_b = result.index("b/b.jpg")
    pos_a = result.index("a/a.jpg")
    assert pos_b < pos_a


def test_gallery_shortcode_reverse():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    img_a = _make_node(
        "/src/photos/a.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={"datetime": "2024-01-01"},
    )
    img_b = _make_node(
        "/src/photos/b.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={"datetime": "2024-01-02"},
    )
    gallery.images = [img_a, img_b]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process('<<gallery sort="datetime" reverse>>', gallery)
    pos_b = result.index("b/b.jpg")
    pos_a = result.index("a/a.jpg")
    assert pos_b < pos_a


def test_gallery_missing_sort_key_sorts_last():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    img_a = _make_node(
        "/src/photos/a.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={"datetime": "2024-01-01"},
    )
    img_b = _make_node(
        "/src/photos/b.jpg",
        NodeType.IMAGE,
        suffix=".jpg",
        metadata={},
    )
    gallery.images = [img_b, img_a]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process('<<gallery sort="datetime">>', gallery)
    pos_a = result.index("a/a.jpg")
    pos_b = result.index("b/b.jpg")
    assert pos_a < pos_b


def test_unknown_shortcode_returns_escaped():
    root = _make_node("/src", NodeType.HOME)
    p = _make_processor(root)
    result = p.process("<<foobar>>", root)
    assert "&lt;&lt;foobar&gt;&gt;" in result


def test_non_shortcode_pattern_returned_unchanged():
    root = _make_node("/src", NodeType.HOME)
    p = _make_processor(root)
    result = p.process("<<.not-a-shortcode>>", root)
    assert "<<.not-a-shortcode>>" in result


def test_malformed_shortcode_returns_escaped():
    root = _make_node("/src", NodeType.HOME)
    p = _make_processor(root)
    result = p.process('<<gallery filter="*.jpg>>', root)
    assert "&lt;&lt;" in result
    assert "&gt;&gt;" in result


def test_gallery_no_images():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    gallery.images = []
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process("<<gallery>>", gallery)
    assert '<div class="gallery">' in result
    assert "<img" not in result


def test_bare_gallery_preserves_order():
    root = _make_node("/src", NodeType.HOME)
    gallery = _make_node("/src/photos", NodeType.GALLERY)
    img_c = _make_node("/src/photos/c.jpg", NodeType.IMAGE, suffix=".jpg", metadata={})
    img_a = _make_node("/src/photos/a.jpg", NodeType.IMAGE, suffix=".jpg", metadata={})
    img_b = _make_node("/src/photos/b.jpg", NodeType.IMAGE, suffix=".jpg", metadata={})
    gallery.images = [img_c, img_a, img_b]
    root.dirs = [gallery]
    p = _make_processor(root)
    result = p.process("<<gallery>>", gallery)
    pos_c = result.index("c/c.jpg")
    pos_a = result.index("a/a.jpg")
    pos_b = result.index("b/b.jpg")
    assert pos_c < pos_a < pos_b
