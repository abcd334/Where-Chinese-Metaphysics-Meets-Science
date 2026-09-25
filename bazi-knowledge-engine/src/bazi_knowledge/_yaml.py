"""Shared strict YAML reader and checkout/wheel knowledge location."""

from importlib.resources import files
from pathlib import Path

import yaml


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently discarding earlier values."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key!r} at {key_node.start_mark}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _knowledge_root(knowledge_dir):
    if knowledge_dir is not None:
        return Path(knowledge_dir)
    root = files("bazi_knowledge").joinpath("knowledge")
    return root if root.is_dir() else Path(__file__).resolve().parents[2] / "knowledge"


def _read_yaml(path):
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(document, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return document
