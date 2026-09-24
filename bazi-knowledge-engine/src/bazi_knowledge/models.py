"""Validated knowledge, relation rules and trace results; no personal interpretation."""

from datetime import date
from typing import Annotated, Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StrictInt, StringConstraints, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
Character = Annotated[str, Field(min_length=1, max_length=1)]
Order = Annotated[StrictInt, Field(ge=1)]
RelationType = Literal["generates", "controls"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class YinYang(DataModel):
    id: Identifier
    name_zh: Character


class Element(DataModel):
    id: Identifier
    name_zh: Character
    order: Order


class HeavenlyStem(DataModel):
    id: Identifier
    char: Character
    order: Order
    yin_yang: Identifier
    element: Identifier


class EarthlyBranch(DataModel):
    id: Identifier
    char: Character
    order: Order
    yin_yang: Identifier
    element: Identifier


class ElementRelation(DataModel):
    source: Identifier
    target: Identifier
    relation: RelationType


class HiddenStemSet(DataModel):
    branch_id: Identifier
    stem_ids: tuple[Identifier, ...] = Field(min_length=1)


class KnowledgeData(DataModel):
    yin_yang: tuple[YinYang, ...] = Field(min_length=2, max_length=2)
    elements: tuple[Element, ...] = Field(min_length=5, max_length=5)
    heavenly_stems: tuple[HeavenlyStem, ...] = Field(min_length=10, max_length=10)
    earthly_branches: tuple[EarthlyBranch, ...] = Field(min_length=12, max_length=12)
    relations: tuple[ElementRelation, ...] = Field(min_length=10, max_length=10)
    hidden_stems: tuple[HiddenStemSet, ...] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_integrity(self) -> Self:
        for name, records, label in (
            ("yin_yang", self.yin_yang, "name_zh"),
            ("elements", self.elements, "name_zh"),
            ("heavenly_stems", self.heavenly_stems, "char"),
            ("earthly_branches", self.earthly_branches, "char"),
        ):
            for field in ("id", label):
                values = [getattr(record, field) for record in records]
                if len(set(values)) != len(values):
                    raise ValueError(f"{name}: duplicate {field}")
            if name != "yin_yang":
                orders = {record.order for record in records}
                if orders != set(range(1, len(records) + 1)):
                    raise ValueError(f"{name}: order must be unique and consecutive from 1")

        yin_yang_ids = {record.id for record in self.yin_yang}
        element_ids = {record.id for record in self.elements}
        for record in (*self.heavenly_stems, *self.earthly_branches):
            if record.yin_yang not in yin_yang_ids or record.element not in element_ids:
                raise ValueError(f"{record.char}: unknown yin_yang or element reference")

        pairs = set()
        for edge in self.relations:
            if edge.source not in element_ids or edge.target not in element_ids:
                raise ValueError("relations: unknown element reference")
            if edge.source == edge.target:
                raise ValueError("relations: self relation is not allowed")
            pair = (edge.source, edge.target)
            if pair in pairs:
                raise ValueError("relations: duplicate or conflicting directed pair")
            pairs.add(pair)
        for kind in ("generates", "controls"):
            edges = [edge for edge in self.relations if edge.relation == kind]
            if (
                len(edges) != len(element_ids)
                or {edge.source for edge in edges} != element_ids
                or {edge.target for edge in edges} != element_ids
            ):
                raise ValueError(f"relations: {kind} needs one incoming/outgoing edge per element")

        branch_ids = {record.id for record in self.earthly_branches}
        stem_ids = {record.id for record in self.heavenly_stems}
        seen_branches = set()
        for record in self.hidden_stems:
            if record.branch_id not in branch_ids:
                raise ValueError(f"hidden_stems: unknown branch reference {record.branch_id!r}")
            if record.branch_id in seen_branches:
                raise ValueError(f"hidden_stems: duplicate branch reference {record.branch_id!r}")
            seen_branches.add(record.branch_id)
            if len(set(record.stem_ids)) != len(record.stem_ids):
                raise ValueError(f"hidden_stems: duplicate stem reference for {record.branch_id!r}")
            if not set(record.stem_ids) <= stem_ids:
                raise ValueError(f"hidden_stems: unknown stem reference for {record.branch_id!r}")
        if seen_branches != branch_ids:
            raise ValueError("hidden_stems: every earthly branch needs a mapping")
        return self


class SourceStatus(DataModel):
    value: Literal["source_attested", "traditional_common", "requires_validation", "derived_from_facts"]
    note: Text


class Source(DataModel):
    id: Identifier
    title: Text
    url: HttpUrl | None
    locator: Text
    scope: Text
    checked_on: date


class FactReference(DataModel):
    collection: Literal["yin_yang", "elements", "heavenly_stems", "earthly_branches"]
    id: Identifier


class TraditionalAssociation(DataModel):
    kind: Literal["symbol", "season", "direction"]
    value: Text
    scope: Text
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    source_status: SourceStatus


class Concept(DataModel):
    id: Identifier
    name_zh: Text
    fact_ref: FactReference | None = None
    short_definition: Text
    plain_explanation: Text
    traditional_associations: tuple[TraditionalAssociation, ...] = ()
    notes: tuple[Text, ...] = ()
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    source_status: SourceStatus


class Season(DataModel):
    id: Literal["spring", "summer", "autumn", "winter"]
    name_zh: Character


class BranchSeason(DataModel):
    branch_id: Identifier
    season_id: Identifier
    stage: Literal["孟", "仲", "季"]
    scope: Text
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    source_status: SourceStatus


class ConceptData(DataModel):
    """A separate schema sharing the same base models and YAML loader as facts."""

    concepts: tuple[Concept, ...] = Field(min_length=1)
    sources: tuple[Source, ...] = Field(min_length=1)
    seasons: tuple[Season, ...] = Field(min_length=4, max_length=4)
    branch_seasons: tuple[BranchSeason, ...] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        for name in ("concepts", "sources", "seasons"):
            records = getattr(self, name)
            if len({record.id for record in records}) != len(records):
                raise ValueError(f"{name}: duplicate id")
        lookup_keys = [key for concept in self.concepts for key in (concept.id, concept.name_zh)]
        if len(set(lookup_keys)) != len(lookup_keys):
            raise ValueError("concepts: ambiguous id or name_zh")
        source_ids = {source.id for source in self.sources}
        season_ids = {season.id for season in self.seasons}
        for record in (*self.concepts, *self.branch_seasons):
            if not set(record.source_ids) <= source_ids:
                raise ValueError("unknown source reference")
        for concept in self.concepts:
            for association in concept.traditional_associations:
                if not set(association.source_ids) <= source_ids:
                    raise ValueError("unknown association source reference")
        for record in self.branch_seasons:
            if record.season_id not in season_ids:
                raise ValueError("unknown season reference")
        if len({record.branch_id for record in self.branch_seasons}) != len(self.branch_seasons):
            raise ValueError("duplicate seasonal branch reference")
        if len({(r.season_id, r.stage) for r in self.branch_seasons}) != 12:
            raise ValueError("each season needs unique 孟/仲/季 positions")
        return self

    def validate_against(self, facts: KnowledgeData) -> Self:
        branch_ids = {branch.id for branch in facts.earthly_branches}
        if {record.branch_id for record in self.branch_seasons} != branch_ids:
            raise ValueError("seasonal mappings must cover exactly the known branches")
        seen_refs = set()
        for concept in self.concepts:
            if concept.fact_ref is None:
                continue
            ref = concept.fact_ref
            record = next((record for record in getattr(facts, ref.collection)
                           if record.id == ref.id), None)
            if record is None:
                raise ValueError(f"unknown concept fact reference: {ref.collection}:{ref.id}")
            if ref.collection == "earthly_branches" and concept.name_zh != record.char:
                raise ValueError("earthly branch concept name must match its fact reference")
            key = (ref.collection, ref.id)
            if key in seen_refs:
                raise ValueError("duplicate concept fact reference")
            seen_refs.add(key)
        required_refs = {
            (collection, record.id)
            for collection in ("yin_yang", "elements", "earthly_branches")
            for record in getattr(facts, collection)
        }
        if not required_refs <= seen_refs:
            raise ValueError("every yin/yang, element and earthly branch needs a concept")
        required = {"yin_yang", "five_elements", "generates", "controls",
                    "heavenly_stems", "earthly_branches", "hidden_stems", "hidden_stems_seasons"}
        if not required <= {concept.id for concept in self.concepts}:
            raise ValueError("missing required overview concept")
        return self


class TraceStep(DataModel):
    operation: Literal["lookup", "join"]
    input_refs: tuple[Text, ...]
    output_refs: tuple[Text, ...]
    source_ids: tuple[Identifier, ...]


class HiddenStemSeasonItem(DataModel):
    stem: HeavenlyStem
    element_concept: Concept


class HiddenStemSeasonContext(DataModel):
    derivation_kind: Literal["reference_join"] = "reference_join"
    branch: EarthlyBranch
    branch_season: BranchSeason
    season: Season
    hidden_stems: tuple[HiddenStemSeasonItem, ...]
    explanation: Concept
    trace: tuple[TraceStep, ...]


TenGodElementRelation = Literal[
    "same", "day_master_generates_target", "day_master_controls_target",
    "target_controls_day_master", "target_generates_day_master",
]
PolarityRelation = Literal["same", "different"]


class TenGod(DataModel):
    """One named outcome and its unique rule; no stem-pair lookup table."""

    id: Identifier
    name_zh: Text
    aliases: tuple[Text, ...] = ()
    element_relation: TenGodElementRelation
    polarity_relation: PolarityRelation
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    source_status: SourceStatus


class TenGodData(DataModel):
    ten_gods: tuple[TenGod, ...] = Field(min_length=10, max_length=10)
    sources: tuple[Source, ...] = Field(min_length=1)
    stem_source_ids: tuple[Identifier, ...] = Field(min_length=1)
    element_source_ids: tuple[Identifier, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rules(self) -> Self:
        for field in ("id", "name_zh"):
            values = [getattr(rule, field) for rule in self.ten_gods]
            if len(set(values)) != len(values):
                raise ValueError(f"ten_gods: duplicate {field}")
        labels = [label for rule in self.ten_gods for label in (rule.name_zh, *rule.aliases)]
        if len(set(labels)) != len(labels):
            raise ValueError("ten_gods: duplicate or conflicting alias")
        combinations = {(rule.element_relation, rule.polarity_relation) for rule in self.ten_gods}
        expected = {(relation, polarity) for relation in get_args(TenGodElementRelation)
                    for polarity in get_args(PolarityRelation)}
        if combinations != expected:
            raise ValueError("ten_gods: each element/polarity combination needs exactly one rule")
        source_ids = {source.id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("ten_gods: duplicate source id")
        for references in (self.stem_source_ids, self.element_source_ids,
                           *(rule.source_ids for rule in self.ten_gods)):
            if not set(references) <= source_ids:
                raise ValueError("ten_gods: unknown source reference")
        return self


class ReasoningStep(DataModel):
    step: Literal["resolve_day_master", "resolve_target", "element_relation",
                  "polarity_relation", "ten_god_rule"]
    input_refs: tuple[Text, ...]
    output_refs: tuple[Text, ...]
    result: Text
    source_ids: tuple[Identifier, ...] = Field(min_length=1)
    element_relation: TenGodElementRelation | None = None
    element_edge: ElementRelation | None = None
    polarity_relation: PolarityRelation | None = None
    rule_id: Identifier | None = None


class TenGodResult(DataModel):
    ten_god: TenGod
    day_master: HeavenlyStem
    target: HeavenlyStem
    element_relation: TenGodElementRelation
    polarity_relation: PolarityRelation
    trace: tuple[ReasoningStep, ...] = Field(min_length=5, max_length=5)
    sources: tuple[Source, ...] = Field(min_length=1)


class HiddenStemTenGodResult(DataModel):
    hidden_stem: HeavenlyStem
    ten_god_result: TenGodResult


class BranchTenGodResult(DataModel):
    """Ordered hidden-stem results; mapping provenance is separate from rule provenance."""

    day_master: HeavenlyStem
    branch: EarthlyBranch
    hidden_stem_results: tuple[HiddenStemTenGodResult, ...] = Field(min_length=1)
    trace: tuple[TraceStep, ...] = Field(min_length=2, max_length=2)
    hidden_stem_source_status: SourceStatus
    sources: tuple[Source, ...] = Field(min_length=1)
