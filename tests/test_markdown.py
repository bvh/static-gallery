from static_gallery.markdown import (
    MarkdownResult,
    render_markdown,
    render_markdown_file,
)


class TestRenderMarkdown:
    def test_basic_rendering(self):
        result = render_markdown("Hello **world**")
        assert result.html == "<p>Hello <strong>world</strong></p>\n"

    def test_html_passthrough(self):
        result = render_markdown('<div class="custom">content</div>')
        assert '<div class="custom">content</div>' in result.html

    def test_empty_markdown(self):
        result = render_markdown("")
        assert result.html == ""
        assert result.title is None

    def test_returns_markdown_result(self):
        result = render_markdown("# Title\n\nBody")
        assert isinstance(result, MarkdownResult)


class TestTitleExtraction:
    def test_extracts_h1_title(self):
        result = render_markdown("# My Title")
        assert result.title == "My Title"

    def test_no_title_when_no_h1(self):
        result = render_markdown("Just a paragraph")
        assert result.title is None

    def test_h2_does_not_set_title(self):
        result = render_markdown("## Not a title")
        assert result.title is None

    def test_only_first_h1_used(self):
        result = render_markdown("# First\n\n# Second")
        assert result.title == "First"

    def test_inline_formatting_stripped(self):
        result = render_markdown("# Hello **world**")
        assert result.title == "Hello world"

    def test_inline_code_stripped(self):
        result = render_markdown("# The `render` function")
        assert result.title == "The render function"


class TestRenderMarkdownFile:
    def test_reads_and_renders_file(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# File Title\n\nSome content")
        result = render_markdown_file(str(md_file))
        assert result.title == "File Title"
        assert "<p>Some content</p>" in result.html

    def test_accepts_path_object(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("Hello")
        result = render_markdown_file(md_file)
        assert "<p>Hello</p>" in result.html

    def test_passes_kwargs_through(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\n\nBody")
        result = render_markdown_file(md_file, extract_title=False)
        assert result.title is None


class TestExtractTitleOption:
    def test_extract_title_false_returns_none(self):
        result = render_markdown("# My Title\n\nBody", extract_title=False)
        assert result.title is None
        assert "<h1>My Title</h1>" in result.html

    def test_extract_title_true_is_default(self):
        result = render_markdown("# My Title")
        assert result.title == "My Title"


class TestRemoveTitle:
    def test_remove_title_strips_h1_from_html(self):
        result = render_markdown("# Title\n\nBody", remove_title=True)
        assert "<h1>" not in result.html
        assert "<p>Body</p>" in result.html

    def test_remove_title_with_extract_title(self):
        result = render_markdown(
            "# Title\n\nBody", extract_title=True, remove_title=True
        )
        assert result.title == "Title"
        assert "<h1>" not in result.html
        assert "<p>Body</p>" in result.html

    def test_remove_title_without_extract_title(self):
        result = render_markdown(
            "# Title\n\nBody", extract_title=False, remove_title=True
        )
        assert result.title is None
        assert "<h1>" not in result.html
        assert "<p>Body</p>" in result.html

    def test_remove_title_no_h1_present(self):
        result = render_markdown("Just a paragraph", remove_title=True)
        assert "<p>Just a paragraph</p>" in result.html

    def test_remove_title_preserves_h2(self):
        result = render_markdown("# Title\n\n## Subtitle\n\nBody", remove_title=True)
        assert "<h1>" not in result.html
        assert "<h2>Subtitle</h2>" in result.html
        assert "<p>Body</p>" in result.html

    def test_remove_title_only_removes_first_h1(self):
        result = render_markdown("# First\n\n# Second", remove_title=True)
        assert "First" not in result.html
        assert "<h1>Second</h1>" in result.html
