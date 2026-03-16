import os

from static_gallery.node import Node, NodeType


class Scanner:
    def __init__(self, config=None, index=None):
        self.config = config
        self._index = index

    def scan(self, path):
        root = Node(os.path.abspath(path), type=NodeType.HOME)
        if root.is_dir():
            self._scan_directory(root)
        else:
            raise ValueError(f"Site path is not a directory: {root.path}.")
        return root

    def _add_to_index(self, node):
        if self._index:
            self._index.add(node)

    def _scan_directory(self, parent):
        count = 0
        # Phase 1: Collect and classify all entries
        dirs = []
        images = []
        markdowns = []
        statics = []

        with os.scandir(parent.path) as path:
            for entry in path:
                # skip dotfiles
                if entry.name.startswith("."):
                    continue
                # skip symlinks
                if entry.is_symlink():
                    continue
                # if name is index.md, it becomes the text source for the
                # container and is not treated as a separate node
                if entry.name.lower() == "index.md":
                    parent.index_path = entry.path
                    parent.mtime = entry.stat().st_mtime
                    count += 1  # container is not empty
                    continue
                # if this is THE site configuration file, load it into
                # the config object and do not treat it as a separate node
                if (
                    entry.name.lower().startswith("site.conf")
                    and parent.type == NodeType.HOME
                ):
                    if self.config and not self.config.config_path:
                        self.config.load_file(entry.path)
                    continue

                child = Node(entry, parent=parent)
                if child.is_dir():
                    if not self._scan_directory(child):
                        continue
                    child.type = (
                        NodeType.GALLERY if child.is_gallery() else NodeType.DIRECTORY
                    )
                    dirs.append(child)
                elif child.is_image():
                    child.type = NodeType.IMAGE
                    images.append(child)
                elif child.is_markdown():
                    child.type = NodeType.MARKDOWN
                    markdowns.append(child)
                else:
                    child.type = NodeType.STATIC
                    statics.append(child)

        # Phase 2: Pair markdown files with images by stem
        image_stems = {img.stem: img for img in images}
        for md in markdowns:
            if md.stem in image_stems:
                image_stems[md.stem].content_path = md.path
            else:
                parent.add_child(md)
                self._add_to_index(md)
                count += 1

        for img in images:
            parent.add_child(img)
            self._add_to_index(img)
            count += 1

        for d in dirs:
            parent.add_child(d)
            self._add_to_index(d)
            count += 1

        for asset in statics:
            parent.add_child(asset)
            self._add_to_index(asset)
            count += 1

        return count
