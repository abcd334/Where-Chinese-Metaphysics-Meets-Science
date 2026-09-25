"""Data-driven, unordered pair matching; no transformation, strength or chart scanning."""

from collections import Counter
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from ._yaml import _knowledge_root, _read_yaml
from .models import (
    DataModel, Source, TraceStep, KnowledgeData,
    PairwiseRule, StemRelation, BranchRelation, StemRelationResult, BranchRelationResult,
)


class InteractionData(DataModel):
    stem_relations: tuple[StemRelation, ...] = Field(min_length=5, max_length=5)
    branch_relations: tuple[BranchRelation, ...] = Field(min_length=12, max_length=12)
    sources: tuple[Source, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rules(self) -> Self:
        rules = (*self.stem_relations, *self.branch_relations)
        if len({rule.id for rule in rules}) != len(rules):
            raise ValueError("interactions: duplicate rule id")
        source_ids = {source.id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("interactions: duplicate source id")
        if any(not set(rule.source_ids) <= source_ids for rule in rules):
            raise ValueError("interactions: unknown source reference")
        keys = {(rule.relation, frozenset(rule.members)) for rule in rules}
        if len(keys) != len(rules):
            raise ValueError("interactions: duplicate unordered rule")
        if Counter(rule.relation for rule in self.branch_relations) != {"six_harmony": 6, "clash": 6}:
            raise ValueError("interactions: requires six harmony and six clash rules")
        return self

    def validate_against(self, facts: KnowledgeData) -> Self:
        for rules, collection in ((self.stem_relations, facts.heavenly_stems),
                                  (self.branch_relations, facts.earthly_branches)):
            known = {item.id for item in collection}
            if any(not set(rule.members) <= known for rule in rules):
                raise ValueError("interactions: unknown member reference in its domain")
            for relation in {rule.relation for rule in rules}:
                members = Counter(member for rule in rules if rule.relation == relation for member in rule.members)
                if members != Counter({member: 1 for member in known}):
                    raise ValueError("interactions: each member needs exactly one partner per relation")
        return self


class InteractionEngine:
    def __init__(self, facts: KnowledgeData, data: InteractionData):
        self.facts = facts
        self.data = data.validate_against(facts)

    @classmethod
    def load(cls, facts: KnowledgeData, knowledge_dir: str | Path | None = None) -> Self:
        root = _knowledge_root(knowledge_dir)
        raw = {}
        for path in (root.joinpath("stem_relations.yaml"), root.joinpath("branch_relations.yaml"),
                     root.joinpath("concepts", "sources.yaml")):
            document = _read_yaml(path)
            if raw.keys() & document.keys():
                raise ValueError(f"{path}: duplicate top-level collection")
            raw.update(document)
        return cls(facts, InteractionData.model_validate(raw))

    @staticmethod
    def _resolve(key, records, collection):
        if not isinstance(key, str):
            raise TypeError(f"{collection}: member must be a character or ID string")
        for record in records:
            if key in (record.id, record.char):
                return record
        raise KeyError(f"Unknown {collection} member: {key!r}")

    def _match(self, first, second, records, rules, collection, rule_collection, result_type):
        members = (self._resolve(first, records, collection), self._resolve(second, records, collection))
        pair = frozenset(member.id for member in members)
        return tuple(result_type(
            rule=rule, members=members,
            trace=(TraceStep(
                operation="lookup", input_refs=tuple(f"{collection}:{member.id}" for member in members),
                output_refs=(f"{rule_collection}:{rule.id}",), source_ids=rule.source_ids,
            ),),
            sources=tuple(source for source in self.data.sources if source.id in rule.source_ids),
        ) for rule in rules if frozenset(rule.members) == pair)

    def get_stem_relations(self, first: str, second: str) -> tuple[StemRelationResult, ...]:
        return self._match(first, second, self.facts.heavenly_stems, self.data.stem_relations,
                           "heavenly_stems", "stem_relations", StemRelationResult)

    def get_branch_relations(self, first: str, second: str) -> tuple[BranchRelationResult, ...]:
        return self._match(first, second, self.facts.earthly_branches, self.data.branch_relations,
                           "earthly_branches", "branch_relations", BranchRelationResult)
