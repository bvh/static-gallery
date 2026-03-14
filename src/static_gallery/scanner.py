import os

from static_gallery.nodes import StaticGalleryNode


def scan(path, config=None):
    # create root node
    root = StaticGalleryNode(os.path.abspath(path), type="HOME")
    if root.is_dir():
        scan_directory(root, config=config)
    else:
        raise ValueError(f"Site path is not a directory: {root.path}.")
    return root


def scan_directory(parent, config=None):
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
                        if config and not config.config_path:
                            config.load_file(entry.path)
                    else:
                        # create the child node, with unknown type
                        child = StaticGalleryNode(entry, parent=parent)
                        if child.is_dir():
                            # if the child is a directory, scan it
                            if not scan_directory(child, config=config):
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
