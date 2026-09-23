"""Read YAML, validate references, and query explicitly stored data."""

from importlib.resources import files
from functools import cached_property
from pathlib import Path

import yaml

from .models import (
    Concept, ConceptData, EarthlyBranch, FactReference, HeavenlyStem,
    HiddenStemSeasonContext, HiddenStemSeasonItem, KnowledgeData, RelationType,
    SourceStatus, TraceStep,
)


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


def load_knowledge(knowledge_dir: str | Path | None = None) -> KnowledgeData:
    """Load the five fact documents, from a checkout or an installed wheel."""
    root = _knowledge_root(knowledge_dir)
    data = {}
    for folder, filename in (
        ("陰陽", "yin_yang.yaml"),
        ("五行", "five_elements.yaml"),
        ("天干", "heavenly_stems.yaml"),
        ("地支", "earthly_branches.yaml"),
        ("", "hidden_stems.yaml"),
    ):
        path = root.joinpath(folder, filename)
        document = _read_yaml(path)
        if data.keys() & document.keys():
            raise ValueError(f"{path}: duplicate top-level collection")
        data.update(document)
    return KnowledgeData.model_validate(data)


def load_concepts(
    knowledge_dir: str | Path | None = None, *, facts: KnowledgeData | None = None,
) -> ConceptData:
    root = _knowledge_root(knowledge_dir).joinpath("concepts")
    data = {}
    for filename in ("sources.yaml", "seasons.yaml", "yin_yang.yaml", "five_elements.yaml",
                     "heavenly_stems.yaml", "earthly_branches.yaml", "hidden_stems.yaml"):
        document = _read_yaml(root.joinpath(filename))
        for key, value in document.items():
            if key == "concepts":
                if not isinstance(value, list):
                    raise ValueError(f"{filename}: concepts must be a YAML list")
                data.setdefault(key, []).extend(value)
            elif key in data:
                raise ValueError(f"{filename}: duplicate top-level collection {key!r}")
            else:
                data[key] = value
    return ConceptData.model_validate(data).validate_against(
        facts if facts is not None else load_knowledge(knowledge_dir)
    )


class KnowledgeBase:
    def __init__(self, knowledge_dir: str | Path | None = None):
        self._knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir is not None else None
        self.data = load_knowledge(knowledge_dir)

    @cached_property
    def concepts(self) -> ConceptData:
        """Concept files are loaded only when requested; fact queries stay independent."""
        return load_concepts(self._knowledge_dir, facts=self.data)

    def get_concept(self, key: str) -> Concept:
        for concept in self.concepts.concepts:
            if key in (concept.id, concept.name_zh):
                return concept
        # Stem definitions are rendered from facts, not a second mapping in YAML.
        for stem in self.data.heavenly_stems:
            if key in (stem.id, stem.char):
                element = next(item for item in self.data.elements if item.id == stem.element)
                polarity = next(item for item in self.data.yin_yang if item.id == stem.yin_yang)
                overview = self.get_concept("heavenly_stems")
                return Concept(
                    id=stem.id, name_zh=stem.char,
                    fact_ref=FactReference(collection="heavenly_stems", id=stem.id),
                    short_definition=f"{stem.char}是十天干第 {stem.order} 位，分類為{polarity.name_zh}{element.name_zh}。",
                    plain_explanation=(f"{stem.char}是天干符號；{element.name_zh}是它的五行分類，"
                                       f"{polarity.name_zh}是它的陰陽分類。這是符號分類，不是個人特質描述。"),
                    notes=overview.notes, source_ids=overview.source_ids,
                    source_status=SourceStatus(value="derived_from_facts", note="由目前載入的天干、五行與陰陽資料組合文字。"),
                )
        raise KeyError(f"Unknown concept: {key!r}")

    def get_hidden_stem_season_context(self, branch: str) -> HiddenStemSeasonContext:
        stems = self.get_hidden_stems(branch)
        record = next(item for item in self.data.earthly_branches if branch in (item.id, item.char))
        seasonal = next(item for item in self.concepts.branch_seasons if item.branch_id == record.id)
        season = next(item for item in self.concepts.seasons if item.id == seasonal.season_id)
        explanation = self.get_concept("hidden_stems_seasons")
        trace = [
            TraceStep(operation="lookup", input_refs=(f"earthly_branches:{record.id}",),
                      output_refs=(f"branch_seasons:{record.id}", f"seasons:{season.id}"),
                      source_ids=seasonal.source_ids),
            TraceStep(operation="lookup", input_refs=(f"hidden_stems:{record.id}",),
                      output_refs=tuple(f"heavenly_stems:{stem.id}" for stem in stems),
                      source_ids=self.get_concept("hidden_stems").source_ids),
        ]
        items = []
        for stem in stems:
            concept = next(item for item in self.concepts.concepts
                           if item.fact_ref == FactReference(collection="elements", id=stem.element))
            items.append(HiddenStemSeasonItem(stem=stem, element_concept=concept))
            trace.append(TraceStep(
                operation="join", input_refs=(f"heavenly_stems:{stem.id}", f"elements:{stem.element}"),
                output_refs=(f"concepts:{concept.id}",),
                source_ids=tuple(dict.fromkeys((*self.get_concept("heavenly_stems").source_ids,
                                               *concept.source_ids,
                                               *(source for association in concept.traditional_associations
                                                 for source in association.source_ids)))),
            ))
        return HiddenStemSeasonContext(branch=record, branch_season=seasonal, season=season,
                                       hidden_stems=tuple(items), explanation=explanation, trace=tuple(trace))

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


def get_concept(key: str) -> Concept:
    return KnowledgeBase().get_concept(key)


def get_hidden_stem_season_context(branch: str) -> HiddenStemSeasonContext:
    return KnowledgeBase().get_hidden_stem_season_context(branch)


def get_generating_element(name_zh: str) -> str:
    return KnowledgeBase().get_generating_element(name_zh)


def get_controlling_element(name_zh: str) -> str:
    return KnowledgeBase().get_controlling_element(name_zh)


def get_element_relation(source: str, target: str) -> RelationType | None:
    return KnowledgeBase().get_element_relation(source, target)
