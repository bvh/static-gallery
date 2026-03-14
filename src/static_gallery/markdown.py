from dataclasses import dataclass

from markdown_it import MarkdownIt


@dataclass
class MarkdownResult:
    html: str
    title: str | None


def render_markdown(text, *, extract_title=True, remove_title=False):
    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(text)
    title = _extract_title(tokens) if extract_title else None
    if remove_title:
        tokens = _remove_first_h1(tokens)
    html = md.renderer.render(tokens, md.options, {})
    return MarkdownResult(html=html, title=title)


def render_markdown_file(path, **kwargs):
    with open(path) as f:
        text = f.read()
    return render_markdown(text, **kwargs)


def _extract_title(tokens):
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1":
            inline = tokens[i + 1]
            parts = []
            for child in inline.children:
                if child.type == "text" or child.type == "code_inline":
                    parts.append(child.content)
            return "".join(parts) or None
    return None


def _remove_first_h1(tokens):
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h1":
            return tokens[:i] + tokens[i + 3 :]
    return tokens
