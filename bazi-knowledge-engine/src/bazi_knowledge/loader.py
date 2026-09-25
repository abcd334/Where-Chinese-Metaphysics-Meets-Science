"""Read YAML, validate references, and query explicitly stored data."""

from math import lcm
from functools import cached_property
from pathlib import Path
from typing import get_args

from ._yaml import _UniqueKeyLoader, _knowledge_root, _read_yaml
from .interactions import InteractionEngine, StemRelationResult, BranchRelationResult

from .models import (
    Concept, ConceptData, EarthlyBranch, FactReference, HeavenlyStem,
    HiddenStemSeasonContext, HiddenStemSeasonItem, KnowledgeData, RelationType,
    SourceStatus, TraceStep,
    ElementRelation, TenGodData, TenGodElementRelation, TenGodResult, ReasoningStep,
    BranchTenGodResult, HiddenStemTenGodResult,
    Pillar, PillarPosition, FourPillars, VisibleStemAnalysis, PillarAnalysis, FourPillarsAnalysis,
)


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


def load_ten_gods(knowledge_dir: str | Path | None = None) -> TenGodData:
    """Read ten rules and the existing source registry without loading concepts."""
    root = _knowledge_root(knowledge_dir)
    data = {}
    for path in (root.joinpath("ten_gods.yaml"), root.joinpath("concepts", "sources.yaml")):
        document = _read_yaml(path)
        if data.keys() & document.keys():
            raise ValueError(f"{path}: duplicate top-level collection")
        data.update(document)
    return TenGodData.model_validate(data)


class KnowledgeBase:
    def __init__(self, knowledge_dir: str | Path | None = None):
        self._knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir is not None else None
        self.data = load_knowledge(knowledge_dir)

    @cached_property
    def concepts(self) -> ConceptData:
        """Concept files are loaded only when requested; fact queries stay independent."""
        return load_concepts(self._knowledge_dir, facts=self.data)

    @cached_property
    def ten_gods(self) -> TenGodData:
        return load_ten_gods(self._knowledge_dir)

    @cached_property
    def interactions(self) -> InteractionEngine:
        return InteractionEngine.load(self.data, self._knowledge_dir)

    def get_stem_relations(self, first: str, second: str) -> tuple[StemRelationResult, ...]:
        return self.interactions.get_stem_relations(first, second)

    def get_branch_relations(self, first: str, second: str) -> tuple[BranchRelationResult, ...]:
        return self.interactions.get_branch_relations(first, second)

    def _ten_god_stem(self, key: str) -> HeavenlyStem:
        if not isinstance(key, str):
            raise TypeError("Ten Gods v0.1 requires a heavenly stem character or ID")
        for stem in self.data.heavenly_stems:
            if key in (stem.char, stem.id):
                return stem
        raise KeyError(f"Unknown heavenly stem: {key!r}")

    def _classify_element_ids(
        self, day_master_id: str, target_id: str,
    ) -> tuple[TenGodElementRelation, ElementRelation | None]:
        if day_master_id == target_id:
            return "same", None
        # These are direction categories, not a second five-element relation table.
        categories = {
            (True, "generates"): "day_master_generates_target",
            (True, "controls"): "day_master_controls_target",
            (False, "generates"): "target_generates_day_master",
            (False, "controls"): "target_controls_day_master",
        }
        matches = []
        for edge in self.data.relations:
            forward = (edge.source, edge.target) == (day_master_id, target_id)
            reverse = (edge.source, edge.target) == (target_id, day_master_id)
            if forward or reverse:
                matches.append((categories[forward, edge.relation], edge))
        if len(matches) != 1:
            raise ValueError("Ten Gods needs exactly one directed relation between distinct elements")
        return matches[0]

    def classify_element_relation(self, day_master_element: str, target_element: str) -> TenGodElementRelation:
        """Classify existing edges from the day master's perspective; accept names or IDs."""
        ids = []
        for key in (day_master_element, target_element):
            if not isinstance(key, str):
                raise TypeError("Element must be a Chinese name or ID")
            element = next((item for item in self.data.elements if key in (item.id, item.name_zh)), None)
            if element is None:
                raise KeyError(f"Unknown element: {key!r}")
            ids.append(element.id)
        return self._classify_element_ids(*ids)[0]

    def get_ten_god(self, day_master: str, target: str) -> TenGodResult:
        """Classify two stems by loaded element edges, polarity and ten YAML rules."""
        dm, other = self._ten_god_stem(day_master), self._ten_god_stem(target)
        relation, edge = self._classify_element_ids(dm.element, other.element)
        polarity = "same" if dm.yin_yang == other.yin_yang else "different"
        rules = self.ten_gods
        rule = next(rule for rule in rules.ten_gods
                    if (rule.element_relation, rule.polarity_relation) == (relation, polarity))
        elements = {item.id: item.name_zh for item in self.data.elements}
        polarities = {item.id: item.name_zh for item in self.data.yin_yang}
        labels = {"same": "同我", "day_master_generates_target": "我生",
                  "day_master_controls_target": "我剋", "target_controls_day_master": "剋我",
                  "target_generates_day_master": "生我"}
        polarity_label = "陰陽相同" if polarity == "same" else "陰陽不同"
        trace = [
            ReasoningStep(
                step=step, input_refs=(f"heavenly_stems:{stem.id}",),
                output_refs=(f"elements:{stem.element}", f"yin_yang:{stem.yin_yang}"),
                result=f"{stem.char} = {polarities[stem.yin_yang]}{elements[stem.element]}",
                source_ids=rules.stem_source_ids,
            )
            for step, stem in (("resolve_day_master", dm), ("resolve_target", other))
        ]
        evidence = (f"{elements[dm.element]}與{elements[other.element]}五行相同" if edge is None else
                    f"{elements[edge.source]}{'生' if edge.relation == 'generates' else '剋'}{elements[edge.target]}")
        trace.extend((
            ReasoningStep(
                step="element_relation", input_refs=(f"elements:{dm.element}", f"elements:{other.element}"),
                output_refs=(f"element_relation:{relation}",), element_relation=relation, element_edge=edge,
                result=f"{evidence}，因此為{labels[relation]}（{relation}）", source_ids=rules.element_source_ids,
            ),
            ReasoningStep(
                step="polarity_relation", input_refs=(f"yin_yang:{dm.yin_yang}", f"yin_yang:{other.yin_yang}"),
                output_refs=(f"polarity_relation:{polarity}",), polarity_relation=polarity,
                result=f"{polarities[dm.yin_yang]} / {polarities[other.yin_yang]}：{polarity_label}（{polarity}）",
                source_ids=rule.source_ids,
            ),
            ReasoningStep(
                step="ten_god_rule", input_refs=(f"element_relation:{relation}", f"polarity_relation:{polarity}"),
                output_refs=(f"ten_gods:{rule.id}",), rule_id=rule.id,
                element_relation=relation, polarity_relation=polarity,
                result=f"{labels[relation]} + {polarity_label} → {rule.name_zh}", source_ids=rule.source_ids,
            ),
        ))
        used_sources = {source for step in trace for source in step.source_ids}
        return TenGodResult(
            ten_god=rule, day_master=dm, target=other, element_relation=relation, polarity_relation=polarity,
            trace=tuple(trace), sources=tuple(source for source in rules.sources if source.id in used_sources),
        )

    def get_concept(self, key: str) -> Concept:
        for concept in self.concepts.concepts:
            if key in (concept.id, concept.name_zh):
                if concept.fact_ref and concept.fact_ref.collection == "earthly_branches":
                    branch = next(item for item in self.data.earthly_branches
                                  if item.id == concept.fact_ref.id)
                    element = next(item for item in self.data.elements if item.id == branch.element)
                    polarity = next(item for item in self.data.yin_yang if item.id == branch.yin_yang)
                    # Only the basic data supplies classification values; keep YAML provenance.
                    return concept.model_copy(update={
                        "short_definition": (
                            f"{concept.short_definition}在本資料集中為第 {branch.order} 位，"
                            f"分類為{polarity.name_zh}{element.name_zh}。"
                        ),
                        "plain_explanation": (
                            f"在目前採用的基本分類中，{polarity.name_zh}是它的陰陽分類，"
                            f"{element.name_zh}是它的五行分類。{concept.plain_explanation}"
                        ),
                    })
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

    def get_branch_ten_gods(self, day_master: str, branch: str) -> BranchTenGodResult:
        """Compose hidden-stem lookup and v0.1 reasoning, preserving stored order."""
        master = self._ten_god_stem(day_master)
        if not isinstance(branch, str):
            raise TypeError("branch requires an earthly branch character or ID")
        stems = self.get_hidden_stems(branch)
        record = next(item for item in self.data.earthly_branches
                      if branch in (item.id, item.char))
        provenance = self.get_concept("hidden_stems")
        items = tuple(HiddenStemTenGodResult(
            hidden_stem=stem, ten_god_result=self.get_ten_god(master.id, stem.id),
        ) for stem in stems)
        trace = (
            TraceStep(operation="lookup", input_refs=(f"earthly_branches:{record.id}",),
                      output_refs=(f"hidden_stems:{record.id}",), source_ids=provenance.source_ids),
            TraceStep(operation="join", input_refs=(f"hidden_stems:{record.id}",),
                      output_refs=tuple(f"heavenly_stems:{stem.id}" for stem in stems),
                      source_ids=provenance.source_ids),
        )
        source_ids = set(provenance.source_ids)
        source_ids.update(source.id for item in items for source in item.ten_god_result.sources)
        return BranchTenGodResult(
            day_master=master, branch=record, hidden_stem_results=items, trace=trace,
            hidden_stem_source_status=provenance.source_status,
            sources=tuple(source for source in self.concepts.sources if source.id in source_ids),
        )

    def generate_sexagenary_cycle(self) -> tuple[Pillar, ...]:
        """Pair ordered stems and branches until both cycles return to their start."""
        stems = sorted(self.data.heavenly_stems, key=lambda stem: stem.order)
        branches = sorted(self.data.earthly_branches, key=lambda branch: branch.order)
        return tuple(Pillar(stem=stems[index % len(stems)], branch=branches[index % len(branches)])
                     for index in range(lcm(len(stems), len(branches))))

    def get_sexagenary_index(self, pillar: str) -> int:
        """Return the one-based cycle index; reject strings outside the generated cycle."""
        if not isinstance(pillar, str):
            raise TypeError("pillar must be a Chinese stem/branch string")
        for index, entry in enumerate(self.generate_sexagenary_cycle(), start=1):
            if pillar == entry.stem.char + entry.branch.char:
                return index
        raise ValueError(f"Invalid sexagenary pillar: {pillar!r}")

    def is_valid_pillar(self, pillar: str) -> bool:
        """Check membership in the generated cycle; non-string inputs raise TypeError."""
        try:
            self.get_sexagenary_index(pillar)
        except ValueError:
            return False
        return True

    def analyze_four_pillars(
        self, *, year: str, month: str, day: str, hour: str,
    ) -> FourPillarsAnalysis:
        """Validate cycle membership and compose existing rules; no date conversion."""
        parsed = {}
        cycle_indices = {}
        for position, value in zip(get_args(PillarPosition), (year, month, day, hour), strict=True):
            if not isinstance(value, str):
                raise TypeError(f"{position}: pillar must be a Chinese stem/branch string")
            if len(value) != 2:
                raise ValueError(f"{position}: pillar must contain exactly two characters")
            try:
                parsed[position] = Pillar(stem=self.get_heavenly_stem(value[0]),
                                          branch=self.get_earthly_branch(value[1]))
            except KeyError as error:
                raise ValueError(f"{position}: expected a known heavenly stem followed by an earthly branch") from error
            try:
                cycle_indices[position] = self.get_sexagenary_index(value)
            except ValueError as error:
                raise ValueError(f"{position}: invalid sexagenary pillar {value!r}") from error
        # Validate all four inputs before running any Layer 2 analysis.
        chart = FourPillars(**parsed)
        master = chart.day.stem
        trace = [TraceStep(
            operation="lookup", input_refs=("chart:input",),
            output_refs=tuple(f"pillars:{position}" for position in parsed), source_ids=(),
        )]
        trace.extend(TraceStep(
            operation="lookup", input_refs=(f"pillars:{position}",),
            output_refs=(f"heavenly_stems:{pillar.stem.id}", f"earthly_branches:{pillar.branch.id}",
                         f"sexagenary_cycle:{cycle_indices[position]}"),
            source_ids=(),
        ) for position, pillar in parsed.items())
        trace.append(TraceStep(
            operation="lookup", input_refs=("pillars:day", f"heavenly_stems:{master.id}"),
            output_refs=(f"day_master:{master.id}",), source_ids=(),
        ))
        analyses = []
        sources = {}
        for position, pillar in parsed.items():
            visible_result = None if position == "day" else self.get_ten_god(master.id, pillar.stem.id)
            branch_result = self.get_branch_ten_gods(master.id, pillar.branch.id)
            analyses.append(PillarAnalysis(
                position=position, pillar=pillar,
                visible_stem_analysis=VisibleStemAnalysis(
                    stem=pillar.stem, role="day_master" if position == "day" else "target",
                    ten_god_result=visible_result,
                ),
                branch_analysis=branch_result,
            ))
            for result in (visible_result, branch_result):
                if result is not None:
                    sources.update((source.id, source) for source in result.sources)
        return FourPillarsAnalysis(chart=chart, day_master=master, pillars=tuple(analyses),
                                   trace=tuple(trace), sources=tuple(sources.values()))

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


def get_stem_relations(first: str, second: str) -> tuple[StemRelationResult, ...]:
    return KnowledgeBase().get_stem_relations(first, second)


def get_branch_relations(first: str, second: str) -> tuple[BranchRelationResult, ...]:
    return KnowledgeBase().get_branch_relations(first, second)


def get_ten_god(day_master: str, target: str) -> TenGodResult:
    return KnowledgeBase().get_ten_god(day_master, target)


def get_branch_ten_gods(day_master: str, branch: str) -> BranchTenGodResult:
    return KnowledgeBase().get_branch_ten_gods(day_master, branch)


def analyze_four_pillars(*, year: str, month: str, day: str, hour: str) -> FourPillarsAnalysis:
    return KnowledgeBase().analyze_four_pillars(year=year, month=month, day=day, hour=hour)


def generate_sexagenary_cycle() -> tuple[Pillar, ...]:
    return KnowledgeBase().generate_sexagenary_cycle()


def is_valid_pillar(pillar: str) -> bool:
    return KnowledgeBase().is_valid_pillar(pillar)


def get_sexagenary_index(pillar: str) -> int:
    return KnowledgeBase().get_sexagenary_index(pillar)


def classify_element_relation(day_master_element: str, target_element: str) -> TenGodElementRelation:
    return KnowledgeBase().classify_element_relation(day_master_element, target_element)


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
