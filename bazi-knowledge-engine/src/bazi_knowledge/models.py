"""Validated basic data only; no derived attributes or interpretation."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
Character = Annotated[str, Field(min_length=1, max_length=1)]
Order = Annotated[StrictInt, Field(ge=1)]
RelationType = Literal["generates", "controls"]


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
