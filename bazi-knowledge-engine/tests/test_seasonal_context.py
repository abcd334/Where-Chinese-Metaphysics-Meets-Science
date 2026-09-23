from pathlib import Path
from shutil import copytree

import pytest
import yaml

from bazi_knowledge import ConceptData, KnowledgeBase, get_hidden_stem_season_context


@pytest.mark.parametrize("char,branch_id,season,stage", [
    ("寅", "yin", "spring", "孟"), ("卯", "mao", "spring", "仲"), ("辰", "chen", "spring", "季"),
    ("巳", "si", "summer", "孟"), ("午", "wu", "summer", "仲"), ("未", "wei", "summer", "季"),
    ("申", "shen", "autumn", "孟"), ("酉", "you", "autumn", "仲"), ("戌", "xu", "autumn", "季"),
    ("亥", "hai", "winter", "孟"), ("子", "zi", "winter", "仲"), ("丑", "chou", "winter", "季"),
])
def test_branch_season_and_canonical_stems(char, branch_id, season, stage):
    kb = KnowledgeBase()
    context = kb.get_hidden_stem_season_context(char)
    assert context == kb.get_hidden_stem_season_context(branch_id)
    assert context.branch.id == branch_id
    assert context.season.id == season
    assert context.branch_season.stage == stage
    assert [item.stem for item in context.hidden_stems] == kb.get_hidden_stems(char)
    for item in context.hidden_stems:
        assert item.stem is kb.get_heavenly_stem(item.stem.char)
        assert item.element_concept.fact_ref.id == item.stem.element


def test_chen_context_keeps_different_relations_separate():
    context = get_hidden_stem_season_context("辰")
    assert context.branch.element == "earth"
    assert context.season.id == "spring"
    assert [item.stem.char for item in context.hidden_stems] == ["戊", "乙", "癸"]
    seasons = [[a.value for a in item.element_concept.traditional_associations if a.kind == "season"]
               for item in context.hidden_stems]
    assert seasons == [["季夏", "四季末／季節轉換"], ["春"], ["冬"]]
    assert context.derivation_kind == "reference_join"
    assert context.explanation.source_status.value == "requires_validation"
    assert "唯一推出" in context.explanation.plain_explanation
    assert context.hidden_stems[0].element_concept.traditional_associations[-1].source_status.value == "requires_validation"


def test_all_trace_references_and_sources_are_resolvable():
    kb = KnowledgeBase()
    references = {
        **{f"earthly_branches:{r.id}": r for r in kb.data.earthly_branches},
        **{f"heavenly_stems:{r.id}": r for r in kb.data.heavenly_stems},
        **{f"elements:{r.id}": r for r in kb.data.elements},
        **{f"hidden_stems:{r.branch_id}": r for r in kb.data.hidden_stems},
        **{f"branch_seasons:{r.branch_id}": r for r in kb.concepts.branch_seasons},
        **{f"seasons:{r.id}": r for r in kb.concepts.seasons},
        **{f"concepts:{r.id}": r for r in kb.concepts.concepts},
    }
    source_ids = {source.id for source in kb.concepts.sources}
    for branch in kb.data.earthly_branches:
        trace = kb.get_hidden_stem_season_context(branch.id).trace
        assert len(trace) == 2 + len(kb.get_hidden_stems(branch.id))
        for step in trace:
            assert step.source_ids and set(step.source_ids) <= source_ids
            assert all(ref in references for ref in (*step.input_refs, *step.output_refs))


@pytest.mark.parametrize("mutation", [
    "missing_branch", "unknown_branch", "duplicate_branch", "unknown_season", "duplicate_stage",
    "unknown_source", "extra_weight",
])
def test_invalid_seasonal_references_are_rejected(mutation):
    kb = KnowledgeBase()
    raw = kb.concepts.model_dump(mode="json")
    records = raw["branch_seasons"]
    if mutation == "missing_branch":
        records.pop()
    elif mutation == "unknown_branch":
        records[0]["branch_id"] = "missing"
    elif mutation == "duplicate_branch":
        records[0]["branch_id"] = records[1]["branch_id"]
    elif mutation == "unknown_season":
        records[0]["season_id"] = "missing"
    elif mutation == "duplicate_stage":
        records[0]["stage"] = records[1]["stage"]
    elif mutation == "unknown_source":
        records[0]["source_ids"] = ["missing"]
    else:
        records[0]["weight"] = 0.6
    with pytest.raises(ValueError):
        ConceptData.model_validate(raw).validate_against(kb.data)


def test_seasonal_join_uses_yaml_not_python_mapping(tmp_path):
    root = Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))
    path = root / "concepts" / "seasons.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Synthetic fixture: exchange two branch IDs without changing fact data.
    records = raw["branch_seasons"]
    records[0]["branch_id"], records[3]["branch_id"] = records[3]["branch_id"], records[0]["branch_id"]
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(root)
    context = kb.get_hidden_stem_season_context("寅")
    assert context.season.id == "summer"
    assert [item.stem.char for item in context.hidden_stems] == ["甲", "丙", "戊"]


def test_seasonal_join_preserves_requires_validation(tmp_path):
    root = Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))
    path = root / "concepts" / "seasons.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["branch_seasons"][0]["source_status"] = {"value": "requires_validation", "note": "Test pending source."}
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    assert KnowledgeBase(root).get_hidden_stem_season_context("寅").branch_season.source_status.value == "requires_validation"


def test_unknown_branch_still_raises_key_error():
    with pytest.raises(KeyError):
        get_hidden_stem_season_context("missing")
