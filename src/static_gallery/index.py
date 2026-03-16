import os


class SuffixIndex:
    def __init__(self, source_path):
        self._source_path = source_path
        self._exact = {}
        self._suffixes = {}

    def add(self, node):
        """Register a node under its full relative path and all suffix paths."""
        rel_path = os.path.relpath(node.path, self._source_path)
        self._exact[rel_path] = node
        parts = rel_path.split(os.sep)
        for i in range(1, len(parts)):
            suffix = os.sep.join(parts[i:])
            self._suffixes.setdefault(suffix, []).append(node)

    @classmethod
    def build_from_tree(cls, root_node, source_path):
        """Build a SuffixIndex by walking an existing node tree."""
        index = cls(source_path)
        cls._walk_tree(root_node, index)
        return index

    @staticmethod
    def _walk_tree(node, index):
        for img in node.images:
            index.add(img)
        for page in node.pages:
            index.add(page)
        for asset in node.assets:
            index.add(asset)
        for d in node.dirs:
            index.add(d)
            SuffixIndex._walk_tree(d, index)

    def resolve(self, path):
        """Resolve a path to a node. Raises ValueError on ambiguity or not-found."""
        rel_path = path.lstrip("/")
        # Exact match first
        target = self._exact.get(rel_path)
        if target is not None:
            return target
        # Absolute paths: exact only
        if path.startswith("/"):
            raise ValueError(f"Shortcode target not found: {path}")
        # Suffix lookup
        candidates = self._suffixes.get(rel_path, [])
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            paths = sorted(
                os.path.relpath(c.path, self._source_path) for c in candidates
            )
            raise ValueError(
                f"Ambiguous shortcode path '{path}' matches: {', '.join(paths)}"
            )
        raise ValueError(f"Shortcode target not found: {path}")
