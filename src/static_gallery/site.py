from static_gallery.index import SuffixIndex


class Site:
    def __init__(self, root, source_path, index=None):
        self.root = root
        self.source_path = source_path
        self._index = index

    @property
    def index(self):
        if self._index is None:
            self._index = SuffixIndex.build_from_tree(self.root, self.source_path)
        return self._index
