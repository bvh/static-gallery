from dataclasses import dataclass

from markdown_it import MarkdownIt


@dataclass
class MarkdownResult:
    html: str
    title: str | None


class MarkdownRenderer:
    def __init__(self):
        self._md = MarkdownIt("commonmark", {"html": True})

    def render(self, text, *, extract_title=True, remove_title=False):
        tokens = self._md.parse(text)
        title = self._extract_title(tokens) if extract_title else None
        if remove_title:
            tokens = self._remove_first_h1(tokens)
        html = self._md.renderer.render(tokens, self._md.options, {})
        return MarkdownResult(html=html, title=title)

    def render_file(self, path, **kwargs):
        with open(path) as f:
            text = f.read()
        return self.render(text, **kwargs)

    def _extract_title(self, tokens):
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h1":
                inline = tokens[i + 1]
                parts = []
                for child in inline.children:
                    if child.type == "text" or child.type == "code_inline":
                        parts.append(child.content)
                return "".join(parts) or None
        return None

    def _remove_first_h1(self, tokens):
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h1":
                return tokens[:i] + tokens[i + 3 :]
        return tokens
