import os

from static_gallery.node import Node


def make_node(path, type, name=None, stem=None, suffix="", metadata=None):
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
