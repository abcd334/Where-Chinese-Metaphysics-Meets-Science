"""Read YAML, validate references, and query explicitly stored data."""

from importlib.resources import files
from pathlib import Path

import yaml

from .models import EarthlyBranch, HeavenlyStem, KnowledgeData, RelationType


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


def load_knowledge(knowledge_dir: str | Path | None = None) -> KnowledgeData:
    """Load all five UTF-8 documents, either from a checkout or an installed wheel."""
    if knowledge_dir is not None:
        root = Path(knowledge_dir)
    else:
        root = files("bazi_knowledge").joinpath("knowledge")
        if not root.is_dir():
            root = Path(__file__).resolve().parents[2] / "knowledge"
    data = {}
    for folder, filename in (
        ("陰陽", "yin_yang.yaml"),
        ("五行", "five_elements.yaml"),
        ("天干", "heavenly_stems.yaml"),
        ("地支", "earthly_branches.yaml"),
        ("", "hidden_stems.yaml"),
    ):
        path = root.joinpath(folder, filename)
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
        if not isinstance(document, dict):
            raise ValueError(f"{path}: expected a YAML mapping")
        if data.keys() & document.keys():
            raise ValueError(f"{path}: duplicate top-level collection")
        data.update(document)
    return KnowledgeData.model_validate(data)


class KnowledgeBase:
    def __init__(self, knowledge_dir: str | Path | None = None):
        self.data = load_knowledge(knowledge_dir)

    def get_heavenly_stem(self, char: str) -> HeavenlyStem:
        for record in self.data.heavenly_stems:
            if record.char == char:
                return record
        raise KeyError(f"Unknown heavenly stem: {char!r}")

    def get_earthly_branch(self, char: str) -> EarthlyBranch:
        for record in self.data.earthly_branches:
            if record.char == char:
                return record
        raise KeyError(f"Unknown earthly branch: {char!r}")

    def get_hidden_stems(self, branch: str) -> list[HeavenlyStem]:
        """Resolve references in stored order; accept a branch character or ID."""
        branch_record = next(
            (record for record in self.data.earthly_branches
             if branch in (record.char, record.id)),
            None,
        )
        if branch_record is None:
            raise KeyError(f"Unknown earthly branch: {branch!r}")
        hidden = next(
            record for record in self.data.hidden_stems
            if record.branch_id == branch_record.id
        )
        stems_by_id = {record.id: record for record in self.data.heavenly_stems}
        return [stems_by_id[stem_id] for stem_id in hidden.stem_ids]

    def _element_id(self, name_zh: str) -> str:
        for record in self.data.elements:
            if record.name_zh == name_zh:
                return record.id
        raise KeyError(f"Unknown element: {name_zh!r}")

    def _related_element(self, name_zh: str, relation: RelationType) -> str:
        source = self._element_id(name_zh)
        edge = next(
            edge for edge in self.data.relations
            if edge.source == source and edge.relation == relation
        )
        return next(record.name_zh for record in self.data.elements if record.id == edge.target)

    def get_generating_element(self, name_zh: str) -> str:
        """Return what this element generates, as a Chinese name."""
        return self._related_element(name_zh, "generates")

    def get_controlling_element(self, name_zh: str) -> str:
        """Return what this element controls, as a Chinese name."""
        return self._related_element(name_zh, "controls")

    def get_element_relation(self, source: str, target: str) -> RelationType | None:
        source_id, target_id = self._element_id(source), self._element_id(target)
        for edge in self.data.relations:
            if edge.source == source_id and edge.target == target_id:
                return edge.relation
        return None


def get_heavenly_stem(char: str) -> HeavenlyStem:
    return KnowledgeBase().get_heavenly_stem(char)


def get_earthly_branch(char: str) -> EarthlyBranch:
    return KnowledgeBase().get_earthly_branch(char)


def get_hidden_stems(branch: str) -> list[HeavenlyStem]:
    return KnowledgeBase().get_hidden_stems(branch)


def get_generating_element(name_zh: str) -> str:
    return KnowledgeBase().get_generating_element(name_zh)


def get_controlling_element(name_zh: str) -> str:
    return KnowledgeBase().get_controlling_element(name_zh)


def get_element_relation(source: str, target: str) -> RelationType | None:
    return KnowledgeBase().get_element_relation(source, target)
