"""Pairwise v0.1: canonical pairs, symmetry, provenance, validation and isolation."""

from itertools import product
from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import (
    BranchRelationResult, KnowledgeBase, StemRelationResult,
    get_branch_relations, get_stem_relations,
)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
COMBINES = ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")
HARMONIES = ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")
CLASHES = ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase()


@pytest.fixture
def knowledge_dir(tmp_path):
    return Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))


def edit_yaml(path, mutate):
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(raw)
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")


@pytest.mark.parametrize("first,second", tuple(product(STEMS, repeat=2)))
def test_all_100_ordered_stem_pairs(kb, first, second):
    results = kb.get_stem_relations(first, second)
    expected = any(set((first, second)) == set(pair) for pair in COMBINES)
    assert len(results) == int(expected)
    if results:
        assert results[0].rule.relation == "combine"
        assert results[0].members == (kb.get_heavenly_stem(first), kb.get_heavenly_stem(second))
        assert kb.get_stem_relations(second, first)[0].rule is results[0].rule


@pytest.mark.parametrize("first,second", tuple(product(BRANCHES, repeat=2)))
def test_all_144_ordered_branch_pairs(kb, first, second):
    expected = [relation for relation, pairs in (("six_harmony", HARMONIES), ("clash", CLASHES))
                if any(set((first, second)) == set(pair) for pair in pairs)]
    results = kb.get_branch_relations(first, second)
    assert [result.rule.relation for result in results] == expected
    for result, reversed_result in zip(results, kb.get_branch_relations(second, first), strict=True):
        assert result.rule is reversed_result.rule
        assert result.members == tuple(reversed(reversed_result.members))


@pytest.mark.parametrize("method,collection,rule_collection,result_type,pairs", [
    ("get_stem_relations", "heavenly_stems", "stem_relations", StemRelationResult, COMBINES),
    ("get_branch_relations", "earthly_branches", "branch_relations", BranchRelationResult, HARMONIES + CLASHES),
])
def test_ids_identity_trace_and_json(kb, method, collection, rule_collection, result_type, pairs):
    facts = {record.char: record for record in getattr(kb.data, collection)}
    rules = {rule.id: rule for rule in getattr(kb.interactions.data, rule_collection)}
    for first, second in pairs:
        left, right = facts[first], facts[second]
        result, = getattr(kb, method)(first, second)
        assert result == getattr(kb, method)(left.id, right.id)[0]
        assert result.members[0] is left and result.members[1] is right
        assert result.rule is rules[result.rule.id]
        assert result.trace[0].input_refs == (f"{collection}:{left.id}", f"{collection}:{right.id}")
        assert result.trace[0].output_refs == (f"{rule_collection}:{result.rule.id}",)
        assert result.trace[0].source_ids == result.rule.source_ids
        assert set(result.rule.members) == {left.id, right.id}
        sources = {source.id: source for source in result.sources}
        assert set(result.rule.source_ids) == sources.keys()
        assert all(source.url is None for source in result.sources)
        assert "user-supplied" in sources["pairwise_v01_spec"].title
        assert result.rule.source_status.value == "requires_validation"
        assert result_type.model_validate_json(result.model_dump_json()) == result


def test_module_wrappers_and_namespace_collisions(kb):
    assert get_stem_relations("丙", "辛") == kb.get_stem_relations("bing", "xin")
    assert get_branch_relations("卯", "戌") == kb.get_branch_relations("mao", "xu")
    assert get_stem_relations("wu", "gui")[0].members[0].char == "戊"
    assert get_branch_relations("wu", "wei")[0].members[0].char == "午"
    assert get_branch_relations("yin", "hai")[0].members[0].char == "寅"
    assert get_stem_relations("甲", "甲") == ()
    assert get_branch_relations("子", "子") == ()


@pytest.mark.parametrize("method,valid,invalid", [
    ("get_stem_relations", "甲", "子"), ("get_stem_relations", "甲", "yin"),
    ("get_branch_relations", "子", "甲"), ("get_branch_relations", "子", "jia"),
    ("get_branch_relations", "子", "branch_yin"), ("get_stem_relations", "甲", "丙辛"),
    ("get_branch_relations", "子", "2026-09-25"), ("get_stem_relations", "甲", ""),
    ("get_branch_relations", "子", ""), ("get_stem_relations", "甲", " 甲"),
])
def test_unknown_or_out_of_domain_input(kb, method, valid, invalid):
    for args in ((valid, invalid), (invalid, valid)):
        with pytest.raises(KeyError):
            getattr(kb, method)(*args)


@pytest.mark.parametrize("invalid", [None, 1, ["甲"], {"char": "甲"}])
def test_non_string_input(kb, invalid):
    for method, valid in ((kb.get_stem_relations, "甲"), (kb.get_branch_relations, "子")):
        with pytest.raises(TypeError):
            method(invalid, valid)
        with pytest.raises(TypeError):
            method(valid, invalid)


@pytest.mark.parametrize("mutation", [
    "missing", "extra", "duplicate_id", "duplicate_pair", "self", "one_member", "three_members",
    "unknown_member", "wrong_domain", "unknown_source", "duplicate_source", "empty_source",
    "invalid_relation", "missing_status", "invalid_status", "wrong_family_count", "missing_coverage",
    "weight", "transformation", "interpretation",
])
def test_bad_rules_are_rejected(knowledge_dir, mutation):
    def mutate(raw):
        rules = raw["branch_relations"]
        rule = rules[0]
        if mutation == "missing":
            rules.pop()
        elif mutation == "extra":
            rules.append(rule.copy())
        elif mutation == "duplicate_id":
            rules[1]["id"] = rule["id"]
        elif mutation == "duplicate_pair":
            rules[1]["members"] = list(reversed(rule["members"]))
        elif mutation == "self":
            rule["members"] = ["zi", "zi"]
        elif mutation == "one_member":
            rule["members"] = ["zi"]
        elif mutation == "three_members":
            rule["members"] = ["zi", "chou", "yin"]
        elif mutation == "unknown_member":
            rule["members"] = ["missing", "chou"]
        elif mutation == "wrong_domain":
            rule["members"] = ["jia", "chou"]
        elif mutation == "unknown_source":
            rule["source_ids"] = ["missing"]
        elif mutation == "duplicate_source":
            rule["source_ids"] *= 2
        elif mutation == "empty_source":
            rule["source_ids"] = []
        elif mutation == "invalid_relation":
            rule["relation"] = "combine"
        elif mutation == "missing_status":
            rule.pop("source_status")
        elif mutation == "invalid_status":
            rule["source_status"]["value"] = "scientific_law"
        elif mutation == "wrong_family_count":
            rule["relation"] = "clash"
        elif mutation == "missing_coverage":
            rule["members"] = ["mao", "chou"]
        else:
            rule[mutation] = "unsupported"
    edit_yaml(knowledge_dir / "branch_relations.yaml", mutate)
    with pytest.raises(ValueError):
        KnowledgeBase(knowledge_dir).get_branch_relations("子", "丑")


@pytest.mark.parametrize("content", ["stem_relations: []\nstem_relations: []", "[]", "stem_relations: ["])
def test_same_strict_yaml_reader(knowledge_dir, content):
    (knowledge_dir / "stem_relations.yaml").write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, yaml.YAMLError)):
        KnowledgeBase(knowledge_dir).get_stem_relations("甲", "己")


def test_duplicate_top_level_and_source_registry_are_rejected(knowledge_dir):
    path = knowledge_dir / "stem_relations.yaml"
    original = path.read_text(encoding="utf-8")
    path.write_text(original + "\nbranch_relations: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate top-level"):
        KnowledgeBase(knowledge_dir).interactions
    path.write_text(original, encoding="utf-8")
    edit_yaml(knowledge_dir / "concepts/sources.yaml", lambda raw: raw["sources"].append(raw["sources"][0].copy()))
    with pytest.raises(ValueError, match="duplicate source id"):
        KnowledgeBase(knowledge_dir).interactions


def test_members_and_provenance_are_data_driven(knowledge_dir):
    def mutate(raw):
        first, second = raw["stem_relations"][:2]
        first["members"][1], second["members"][1] = second["members"][1], first["members"][1]
        first["source_ids"] = ["concept_spec"]
        first["source_status"]["note"] = "Synthetic pending pair."
    edit_yaml(knowledge_dir / "stem_relations.yaml", mutate)
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_stem_relations("甲", "己") == ()
    result, = kb.get_stem_relations("甲", "庚")
    assert result.rule.source_status.note == "Synthetic pending pair."
    assert result.rule.source_status.value == "requires_validation"
    assert result.trace[0].source_ids == ("concept_spec",)
    assert [source.id for source in result.sources] == ["concept_spec"]


def test_old_apis_and_four_pillars_do_not_load_interaction_files(knowledge_dir):
    for name in ("stem_relations.yaml", "branch_relations.yaml"):
        (knowledge_dir / name).unlink()
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_heavenly_stem("甲").element == "wood"
    assert kb.get_hidden_stems("寅")[0].char == "甲"
    assert kb.get_ten_god("壬", "乙").ten_god.name_zh == "傷官"
    assert kb.get_branch_ten_gods("壬", "戌").branch.char == "戌"
    assert kb.is_valid_pillar("甲子") is True
    result = kb.analyze_four_pillars(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
    assert result.day_master.char == "壬"
    assert "interactions" not in kb.__dict__
    with pytest.raises(FileNotFoundError):
        kb.get_stem_relations("甲", "己")


def test_only_rules_and_source_registry_are_loaded(knowledge_dir, monkeypatch):
    (knowledge_dir / "concepts/seasons.yaml").unlink()
    (knowledge_dir / "ten_gods.yaml").unlink()
    monkeypatch.chdir(knowledge_dir.parent)
    kb = KnowledgeBase("knowledge")
    monkeypatch.chdir(knowledge_dir)
    assert kb.get_stem_relations("甲", "己")[0].rule.relation == "combine"
    assert kb.get_branch_relations("辰", "戌")[0].rule.relation == "clash"
    assert "concepts" not in kb.__dict__ and "ten_gods" not in kb.__dict__


def test_result_scope_and_immutability(kb):
    result = kb.get_branch_relations("卯", "戌")[0]
    for record in (result, result.rule):
        for field in ("transformed_element", "weight", "fortune", "strength", "pillar_positions"):
            with pytest.raises(ValidationError, match="Extra inputs"):
                type(record).model_validate({**record.model_dump(), field: "unsupported"})
    with pytest.raises(ValidationError, match="frozen"):
        result.members = ()
