from collections import Counter
from itertools import product
from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import (
    KnowledgeBase, TenGod, TenGodResult, classify_element_relation, get_ten_god, load_ten_gods,
)


NAMES = ("比肩", "劫財", "食神", "傷官", "偏財", "正財", "七殺", "正官", "偏印", "正印")
STEMS = "甲乙丙丁戊己庚辛壬癸"


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


@pytest.mark.parametrize("day_master,targets", [("壬", "壬癸甲乙丙丁戊己庚辛"), ("甲", STEMS)])
@pytest.mark.parametrize("index,name", tuple(enumerate(NAMES)))
def test_canonical_day_master_examples(kb, day_master, targets, index, name):
    assert kb.get_ten_god(day_master, targets[index]).ten_god.name_zh == name


@pytest.mark.parametrize("day_master,target", tuple(product(STEMS, repeat=2)))
def test_all_100_stem_pairs_resolve_uniquely_and_have_trace(kb, day_master, target):
    result = kb.get_ten_god(day_master, target)
    assert isinstance(result.ten_god, TenGod)
    assert result.day_master is kb.get_heavenly_stem(day_master)
    assert result.target is kb.get_heavenly_stem(target)
    matches = [rule for rule in kb.ten_gods.ten_gods if
               (rule.element_relation, rule.polarity_relation) ==
               (result.element_relation, result.polarity_relation)]
    assert matches == [result.ten_god]
    assert result.ten_god is matches[0]
    assert len(result.trace) == 5
    assert result.trace[-1].rule_id == result.ten_god.id
    assert result.trace[-1].element_relation == result.element_relation
    assert result.trace[-1].polarity_relation == result.polarity_relation
    refs = {f"{collection}:{item.id}" for collection in ("heavenly_stems", "elements", "yin_yang")
            for item in getattr(kb.data, collection)}
    refs.update((f"element_relation:{result.element_relation}",
                 f"polarity_relation:{result.polarity_relation}", f"ten_gods:{result.ten_god.id}"))
    sources = {source.id for source in result.sources}
    for step in result.trace:
        assert set((*step.input_refs, *step.output_refs)) <= refs
        assert step.source_ids and set(step.source_ids) <= sources
    assert TenGodResult.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("day_master", STEMS)
def test_each_day_master_covers_each_ten_god_once(kb, day_master):
    results = [kb.get_ten_god(day_master, target).ten_god.name_zh for target in STEMS]
    assert Counter(results) == Counter(NAMES)


@pytest.mark.parametrize("target,relation", [
    ("水", "same"), ("木", "day_master_generates_target"),
    ("火", "day_master_controls_target"), ("土", "target_controls_day_master"),
    ("金", "target_generates_day_master"),
])
def test_direction_categories(kb, target, relation):
    assert classify_element_relation("水", target) == relation
    target_id = next(item.id for item in kb.data.elements if item.name_zh == target)
    assert kb.classify_element_relation("water", target_id) == relation


@pytest.mark.parametrize("target,stem_id,element,edge_source,edge_target,category,name", [
    ("乙", "yi", "wood", "water", "wood", "day_master_generates_target", "傷官"),
    ("辛", "xin", "metal", "metal", "water", "target_generates_day_master", "正印"),
])
def test_requested_traces(kb, target, stem_id, element, edge_source, edge_target, category, name):
    result = get_ten_god("壬", target)
    dm, other, relation, polarity, conclusion = result.trace
    assert dm.step == "resolve_day_master" and dm.result == "壬 = 陽水"
    assert dm.input_refs == ("heavenly_stems:ren",)
    assert dm.output_refs == ("elements:water", "yin_yang:yang")
    assert other.input_refs == (f"heavenly_stems:{stem_id}",)
    assert other.output_refs == (f"elements:{element}", "yin_yang:yin")
    assert other.result == ("乙 = 陰木" if target == "乙" else "辛 = 陰金")
    assert relation.element_edge.model_dump() == {
        "source": edge_source, "target": edge_target, "relation": "generates",
    }
    assert relation.element_edge in kb.data.relations
    assert relation.element_relation == category
    assert polarity.input_refs == ("yin_yang:yang", "yin_yang:yin")
    assert polarity.polarity_relation == "different"
    assert conclusion.rule_id == result.ten_god.id
    assert conclusion.input_refs == (f"element_relation:{category}", "polarity_relation:different")
    assert conclusion.output_refs == (f"ten_gods:{result.ten_god.id}",)
    assert result.ten_god.name_zh == name
    assert result.ten_god.source_status.value == "requires_validation"


def test_same_element_trace_does_not_invent_an_edge(kb):
    result = kb.get_ten_god("壬", "癸")
    assert result.element_relation == "same"
    assert result.trace[2].element_edge is None
    assert "五行相同" in result.trace[2].result


def test_ids_and_aliases_preserve_canonical_results(kb):
    assert get_ten_god("ren", "yi") == kb.get_ten_god("壬", "乙")
    assert kb.get_ten_god("ren", "wu").target.char == "戊"
    rule = kb.get_ten_god("壬", "戊").ten_god
    assert (rule.id, rule.name_zh, rule.aliases) == ("qi_sha", "七殺", ("偏官",))


@pytest.mark.parametrize("invalid", ["子", "寅", "午", "yin", "zi", "壬乙", "2026-09-24", "偏官", ""])
@pytest.mark.parametrize("position", [0, 1])
def test_non_stem_names_are_rejected(kb, invalid, position):
    args = ["壬", "乙"]
    args[position] = invalid
    with pytest.raises(KeyError):
        kb.get_ten_god(*args)


@pytest.mark.parametrize("invalid", [None, 1, ["壬"], {"char": "壬"}])
def test_non_string_inputs_are_rejected(kb, invalid):
    with pytest.raises(TypeError):
        kb.get_ten_god(invalid, "乙")
    with pytest.raises(TypeError):
        kb.get_ten_god("壬", invalid)
    with pytest.raises(TypeError):
        kb.get_ten_god("壬", kb.get_earthly_branch("子"))


@pytest.mark.parametrize("mutation", [
    "missing", "extra", "duplicate_id", "duplicate_name", "duplicate_predicate", "invalid_element",
    "invalid_polarity", "unknown_source", "unknown_stem_source", "unknown_element_source",
    "empty_source", "bad_status", "duplicate_alias", "conflicting_alias", "extra_field",
])
def test_bad_rules_are_rejected_during_loading(knowledge_dir, mutation):
    def mutate(raw):
        rules = raw["ten_gods"]
        if mutation == "missing":
            rules.pop()
        elif mutation == "extra":
            rules.append(rules[0].copy())
        elif mutation == "duplicate_id":
            rules[1]["id"] = rules[0]["id"]
        elif mutation == "duplicate_name":
            rules[1]["name_zh"] = rules[0]["name_zh"]
        elif mutation == "duplicate_predicate":
            rules[1]["polarity_relation"] = rules[0]["polarity_relation"]
        elif mutation == "invalid_element":
            rules[0]["element_relation"] = "indirect"
        elif mutation == "invalid_polarity":
            rules[0]["polarity_relation"] = "male"
        elif mutation == "unknown_source":
            rules[0]["source_ids"] = ["missing"]
        elif mutation == "unknown_stem_source":
            raw["stem_source_ids"] = ["missing"]
        elif mutation == "unknown_element_source":
            raw["element_source_ids"] = ["missing"]
        elif mutation == "empty_source":
            rules[0]["source_ids"] = []
        elif mutation == "bad_status":
            rules[0]["source_status"]["value"] = "scientific_law"
        elif mutation == "duplicate_alias":
            rules[0]["aliases"] = ["同名", "同名"]
        elif mutation == "conflicting_alias":
            rules[0]["aliases"] = [rules[1]["name_zh"]]
        else:
            rules[0]["personality"] = "unsupported"
    edit_yaml(knowledge_dir / "ten_gods.yaml", mutate)
    with pytest.raises(ValidationError):
        load_ten_gods(knowledge_dir)


def test_rule_selection_and_status_come_from_yaml(knowledge_dir):
    def mutate(raw):
        first, second = raw["ten_gods"][2:4]
        first["polarity_relation"], second["polarity_relation"] = second["polarity_relation"], first["polarity_relation"]
        first["source_status"]["note"] = "測試：待驗證規則。"
    edit_yaml(knowledge_dir / "ten_gods.yaml", mutate)
    result = KnowledgeBase(knowledge_dir).get_ten_god("壬", "乙")
    assert result.ten_god.name_zh == "食神"  # Synthetic fixture, not canonical knowledge.
    assert result.trace[-1].rule_id == "shi_shen"
    assert result.ten_god.source_status.note == "測試：待驗證規則。"
    assert result.ten_god.source_status.value == "requires_validation"


def test_element_edges_come_from_existing_yaml(knowledge_dir):
    def mutate(raw):
        for edge in raw["relations"]:
            edge["relation"] = "controls" if edge["relation"] == "generates" else "generates"
    edit_yaml(knowledge_dir / "五行/five_elements.yaml", mutate)
    result = KnowledgeBase(knowledge_dir).get_ten_god("壬", "乙")
    assert result.ten_god.name_zh == "正財"
    assert result.element_relation == "day_master_controls_target"
    assert result.trace[2].element_edge.relation == "controls"


@pytest.mark.parametrize("attribute,value,name", [("element", "water", "劫財"), ("yin_yang", "yang", "食神")])
def test_stem_attributes_come_from_basic_yaml(knowledge_dir, attribute, value, name):
    def mutate(raw):
        raw["heavenly_stems"][1][attribute] = value
    edit_yaml(knowledge_dir / "天干/heavenly_stems.yaml", mutate)
    result = KnowledgeBase(knowledge_dir).get_ten_god("壬", "乙")
    assert result.ten_god.name_zh == name
    assert getattr(result.target, attribute) == value


@pytest.mark.parametrize("target", ["甲", "丙"])
def test_missing_or_ambiguous_element_directions_fail_explicitly(knowledge_dir, target):
    def mutate(raw):
        generates = [edge for edge in raw["relations"] if edge["relation"] == "generates"]
        raw["relations"] = generates + [
            {"source": edge["target"], "target": edge["source"], "relation": "controls"} for edge in generates
        ]
    edit_yaml(knowledge_dir / "五行/five_elements.yaml", mutate)
    kb = KnowledgeBase(knowledge_dir)  # Existing Layer 1 validation remains unchanged.
    with pytest.raises(ValueError, match="exactly one directed relation"):
        kb.get_ten_god("壬", target)


@pytest.mark.parametrize("content", ["ten_gods: []\nten_gods: []", "[]", "ten_gods: ["])
def test_new_yaml_uses_strict_reader(knowledge_dir, content):
    (knowledge_dir / "ten_gods.yaml").write_text(content, encoding="utf-8")
    with pytest.raises((ValueError, yaml.YAMLError)):
        load_ten_gods(knowledge_dir)


def test_missing_ten_gods_file_does_not_break_old_apis(knowledge_dir):
    (knowledge_dir / "ten_gods.yaml").unlink()
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_heavenly_stem("壬").element == "water"
    assert kb.get_earthly_branch("寅").element == "wood"
    assert len(kb.get_hidden_stems("寅")) == 3
    assert kb.get_element_relation("水", "木") == "generates"
    assert kb.get_concept("寅").name_zh == "寅"
    with pytest.raises(FileNotFoundError):
        kb.get_ten_god("壬", "乙")


def test_rules_need_only_source_registry_not_concept_or_season_data(knowledge_dir, monkeypatch):
    (knowledge_dir / "concepts/seasons.yaml").unlink()
    monkeypatch.chdir(knowledge_dir.parent)
    kb = KnowledgeBase("knowledge")
    monkeypatch.chdir(knowledge_dir)
    assert kb.get_ten_god("ren", "xin").ten_god.name_zh == "正印"


def test_source_registry_integrity_is_checked(knowledge_dir):
    def mutate(raw):
        raw["sources"].append(raw["sources"][0].copy())
    edit_yaml(knowledge_dir / "concepts/sources.yaml", mutate)
    with pytest.raises(ValidationError, match="duplicate source id"):
        load_ten_gods(knowledge_dir)


def test_ten_gods_provenance_and_content_boundary(kb):
    data = kb.ten_gods
    assert len(data.ten_gods) == 10
    assert {rule.name_zh for rule in data.ten_gods} == set(NAMES)
    assert {rule.id for rule in data.ten_gods} == {
        "bi_jian", "jie_cai", "shi_shen", "shang_guan", "pian_cai", "zheng_cai",
        "qi_sha", "zheng_guan", "pian_yin", "zheng_yin",
    }
    source = next(s for s in data.sources if s.id == "ten_gods_v01_spec")
    assert source.url is None
    assert "user-supplied canonical implementation specification" in source.title
    for rule in data.ten_gods:
        assert rule.source_ids == (source.id,)
        assert rule.source_status.value == "requires_validation"
    result = kb.get_ten_god("壬", "乙")
    for record in (result.ten_god, result, *result.trace):
        for field in ("personality", "career", "wealth", "marriage", "health_prediction", "fortune", "luck"):
            with pytest.raises(ValidationError, match="Extra inputs"):
                type(record).model_validate({**record.model_dump(), field: "unsupported"})
