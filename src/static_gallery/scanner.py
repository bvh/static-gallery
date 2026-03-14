import os

from static_gallery.nodes import Node


class Scanner:
    def __init__(self, config=None):
        self.config = config

    def scan(self, path):
        root = Node(os.path.abspath(path), type="HOME")
        if root.is_dir():
            self._scan_directory(root)
        else:
            raise ValueError(f"Site path is not a directory: {root.path}.")
        return root

    def _scan_directory(self, parent):
        count = 0
        with os.scandir(parent.path) as path:
            for entry in path:
                # skip dotfiles
                if not entry.name.startswith("."):
                    # skip symlinks
                    if not entry.is_symlink():
                        # if name is index.md, it becomes the text source for the
                        # container and is not treated as a separate node
                        if entry.name.lower() == "index.md":
                            parent.text = entry.path
                            parent.mtime = entry.stat().st_mtime
                            count += 1  # container is not empty
                        # if this is THE site configuration file, load it into
                        # the config object and do not treat it as a separate node
                        elif (
                            entry.name.lower().startswith("site.conf")
                            and parent.type == "HOME"
                        ):
                            if self.config and not self.config.config_path:
                                self.config.load_file(entry.path)
                        else:
                            # create the child node, with unknown type
                            child = Node(entry, parent=parent)
                            if child.is_dir():
                                # if the child is a directory, scan it
                                if not self._scan_directory(child):
                                    # if the directory is empty, skip it
                                    continue
                                # directories containing only images are galleries
                                child.type = (
                                    "GALLERY" if child.is_gallery() else "DIRECTORY"
                                )
                            # if not a directory, figure out what type it is
                            elif child.is_markdown():
                                child.type = "MARKDOWN"
                            elif child.is_image():
                                child.type = "IMAGE"
                            else:
                                # if not markdown or an image, must be static
                                child.type = "STATIC"
                            # add the child
                            parent.add_child(child)
                            count += 1  # container is not empty
        return count
