"""Ten Gods v0.2 composition, provenance, ordering and input boundaries."""

from itertools import product
from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import BranchTenGodResult, KnowledgeBase, get_branch_ten_gods


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


def test_ren_xu_results_and_complete_reasoning(kb):
    result = get_branch_ten_gods("壬", "戌")
    assert result == kb.get_branch_ten_gods("ren", "xu")
    assert [(item.hidden_stem.char, item.ten_god_result.ten_god.name_zh)
            for item in result.hidden_stem_results] == [("戊", "七殺"), ("辛", "正印"), ("丁", "正財")]
    expected = [
        ("戊 = 陽土", "earth", "water", "controls", "target_controls_day_master", "same", "qi_sha"),
        ("辛 = 陰金", "metal", "water", "generates", "target_generates_day_master", "different", "zheng_yin"),
        ("丁 = 陰火", "water", "fire", "controls", "day_master_controls_target", "different", "zheng_cai"),
    ]
    for item, (text, source, target, relation, category, polarity, rule) in zip(
        result.hidden_stem_results, expected, strict=True,
    ):
        dm, stem, edge, comparison, conclusion = item.ten_god_result.trace
        assert dm.result == "壬 = 陽水" and stem.result == text
        assert edge.element_edge.model_dump() == {"source": source, "target": target, "relation": relation}
        assert edge.element_relation == category
        assert comparison.polarity_relation == polarity
        assert conclusion.rule_id == rule


@pytest.mark.parametrize("day_master,branch", tuple(product("甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥")))
def test_all_120_pairs_preserve_order_identity_and_v01_results(kb, day_master, branch):
    result = kb.get_branch_ten_gods(day_master, branch)
    assert result.day_master is kb.get_heavenly_stem(day_master)
    assert result.branch is kb.get_earthly_branch(branch)
    stems = kb.get_hidden_stems(branch)
    assert len(result.hidden_stem_results) == len(stems)
    for item, stem in zip(result.hidden_stem_results, stems, strict=True):
        assert item.hidden_stem is stem
        assert item.ten_god_result.target is stem
        assert item.ten_god_result.day_master is result.day_master
        assert item.ten_god_result == kb.get_ten_god(day_master, stem.id)
    assert result == kb.get_branch_ten_gods(result.day_master.id, result.branch.id)
    assert BranchTenGodResult.model_validate_json(result.model_dump_json()) == result


def test_lookup_trace_and_all_sources_resolve(kb):
    references = {f"earthly_branches:{b.id}" for b in kb.data.earthly_branches}
    references.update(f"hidden_stems:{h.branch_id}" for h in kb.data.hidden_stems)
    references.update(f"heavenly_stems:{s.id}" for s in kb.data.heavenly_stems)
    for branch in kb.data.earthly_branches:
        result = kb.get_branch_ten_gods("壬", branch.id)
        lookup, join = result.trace
        assert lookup.input_refs == (f"earthly_branches:{branch.id}",)
        assert lookup.output_refs == join.input_refs == (f"hidden_stems:{branch.id}",)
        assert join.output_refs == tuple(f"heavenly_stems:{i.hidden_stem.id}" for i in result.hidden_stem_results)
        sources = {source.id: source for source in result.sources}
        for step in result.trace:
            assert set((*step.input_refs, *step.output_refs)) <= references
            assert step.source_ids == kb.get_concept("hidden_stems").source_ids
            assert set(step.source_ids) <= sources.keys()
        assert sources[lookup.source_ids[0]].locator.startswith("knowledge/hidden_stems.yaml")
        assert result.hidden_stem_source_status == kb.get_concept("hidden_stems").source_status
        for item in result.hidden_stem_results:
            nested = item.ten_god_result
            assert nested.trace[1].input_refs == (f"heavenly_stems:{item.hidden_stem.id}",)
            assert nested.ten_god.source_status.value == "requires_validation"
            assert all(sources[source.id] == source for source in nested.sources)
            assert all(set(step.source_ids) <= sources.keys() for step in nested.trace)


def test_composition_calls_existing_apis_and_keeps_returned_objects(monkeypatch):
    kb = KnowledgeBase()
    lookup, compute = kb.get_hidden_stems, kb.get_ten_god
    lookup_calls, computed = [], []

    def tracked_lookup(branch):
        lookup_calls.append(branch)
        return lookup(branch)

    def tracked_compute(day_master, target):
        result = compute(day_master, target)
        computed.append(result)
        return result

    monkeypatch.setattr(kb, "get_hidden_stems", tracked_lookup)
    monkeypatch.setattr(kb, "get_ten_god", tracked_compute)
    result = kb.get_branch_ten_gods("壬", "戌")
    assert lookup_calls == ["戌"] and len(computed) == 3
    assert all(item.ten_god_result is original for item, original in zip(
        result.hidden_stem_results, computed, strict=True,
    ))


def test_membership_order_and_provenance_follow_custom_yaml(knowledge_dir):
    def change_mapping(raw):
        next(h for h in raw["hidden_stems"] if h["branch_id"] == "xu")["stem_ids"] = ["ding", "jia"]

    def change_provenance(raw):
        concept = next(c for c in raw["concepts"] if c["id"] == "hidden_stems")
        concept["source_ids"] = ["concept_spec"]
        concept["source_status"] = {"value": "requires_validation", "note": "Synthetic pending mapping."}

    edit_yaml(knowledge_dir / "hidden_stems.yaml", change_mapping)
    edit_yaml(knowledge_dir / "concepts/hidden_stems.yaml", change_provenance)
    result = KnowledgeBase(knowledge_dir).get_branch_ten_gods("壬", "戌")
    assert [(i.hidden_stem.char, i.ten_god_result.ten_god.name_zh) for i in result.hidden_stem_results] == [
        ("丁", "正財"), ("甲", "食神"),
    ]
    assert result.trace[1].output_refs == ("heavenly_stems:ding", "heavenly_stems:jia")
    assert all(step.source_ids == ("concept_spec",) for step in result.trace)
    assert result.hidden_stem_source_status.value == "requires_validation"
    assert result.hidden_stem_source_status.note == "Synthetic pending mapping."


def test_branch_surface_attributes_do_not_determine_ten_gods(knowledge_dir, kb):
    def mutate(raw):
        branch = next(b for b in raw["earthly_branches"] if b["id"] == "xu")
        branch.update(element="wood", yin_yang="yin")
    edit_yaml(knowledge_dir / "地支/earthly_branches.yaml", mutate)
    result = KnowledgeBase(knowledge_dir).get_branch_ten_gods("壬", "戌")
    assert result.branch.element == "wood" and result.branch.yin_yang == "yin"
    assert result.hidden_stem_results == kb.get_branch_ten_gods("壬", "戌").hidden_stem_results


def test_id_collisions_use_argument_namespace(kb):
    result = kb.get_branch_ten_gods("wu", "wu")
    assert (result.day_master.char, result.branch.char) == ("戊", "午")
    assert kb.get_branch_ten_gods("ren", "yin").branch.char == "寅"
    with pytest.raises(KeyError):
        kb.get_branch_ten_gods("yin", "xu")


@pytest.mark.parametrize("master,branch", [
    ("子", "戌"), ("ren", "甲"), ("ren", "jia"), ("ren", "branch_xu"),
    ("", "戌"), ("壬", ""), ("unknown", "戌"), ("壬", "unknown"),
    ("壬", "2026-09-24"), ("丙寅 辛卯 壬戌 乙巳", "戌"),
])
def test_unknown_or_out_of_scope_inputs_raise_key_error(kb, master, branch):
    with pytest.raises(KeyError):
        kb.get_branch_ten_gods(master, branch)


@pytest.mark.parametrize("invalid", [None, 12, ["戌"], {"char": "戌"}])
def test_non_string_inputs_raise_type_error(kb, invalid):
    with pytest.raises(TypeError):
        kb.get_branch_ten_gods(invalid, "戌")
    with pytest.raises(TypeError):
        kb.get_branch_ten_gods("壬", invalid)


def test_nested_failure_is_not_silently_returned_as_partial_success(monkeypatch):
    kb = KnowledgeBase()
    compute = kb.get_ten_god

    def failing_compute(master, target):
        if target == "xin":
            raise ValueError("Synthetic rule failure")
        return compute(master, target)

    monkeypatch.setattr(kb, "get_ten_god", failing_compute)
    with pytest.raises(ValueError, match="Synthetic rule failure"):
        kb.get_branch_ten_gods("壬", "戌")


@pytest.mark.parametrize("field", ["weight", "percentage", "qi_classification", "strength", "fortune"])
def test_results_reject_weighting_and_interpretation_fields(kb, field):
    result = kb.get_branch_ten_gods("壬", "戌")
    for record in (result, result.hidden_stem_results[0]):
        with pytest.raises(ValidationError, match="Extra inputs"):
            type(record).model_validate({**record.model_dump(), field: "unsupported"})


def test_result_is_immutable(kb):
    result = kb.get_branch_ten_gods("壬", "戌")
    with pytest.raises(ValidationError, match="frozen"):
        result.hidden_stem_results = ()
