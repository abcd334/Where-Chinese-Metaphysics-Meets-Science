"""Layer 1 v1.0 acceptance: coverage, references, provenance and scope."""

from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import Concept, KnowledgeBase, get_concept, load_concepts


@pytest.fixture
def knowledge_dir(tmp_path):
    return Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))


@pytest.mark.parametrize("collection,count", [
    ("yin_yang", 2), ("elements", 5), ("heavenly_stems", 10), ("earthly_branches", 12),
])
def test_every_basic_element_has_explanation_and_resolvable_provenance(collection, count):
    kb = KnowledgeBase()
    facts = getattr(kb.data, collection)
    assert len(facts) == count
    sources = {source.id: source for source in kb.concepts.sources}
    for fact in facts:
        key = fact.name_zh if collection in ("yin_yang", "elements") else fact.char
        concept = kb.get_concept(key)
        assert (concept.fact_ref.collection, concept.fact_ref.id) == (collection, fact.id)
        assert concept.short_definition.strip() and concept.plain_explanation.strip()
        assert concept.source_status.note.strip()
        assert concept.source_ids
        for source_id in concept.source_ids:
            source = sources[source_id]
            assert source.title and source.locator and source.scope and source.checked_on


@pytest.mark.parametrize("char,branch_id,order,classification", [
    ("子", "zi", 1, "陽水"), ("丑", "chou", 2, "陰土"),
    ("寅", "yin", 3, "陽木"), ("卯", "mao", 4, "陰木"),
    ("辰", "chen", 5, "陽土"), ("巳", "si", 6, "陰火"),
    ("午", "wu", 7, "陽火"), ("未", "wei", 8, "陰土"),
    ("申", "shen", 9, "陽金"), ("酉", "you", 10, "陰金"),
    ("戌", "xu", 11, "陽土"), ("亥", "hai", 12, "陰水"),
])
def test_individual_branch_lookup(char, branch_id, order, classification):
    concept = get_concept(char)
    assert concept == KnowledgeBase().get_concept(f"branch_{branch_id}")
    assert concept.id == f"branch_{branch_id}"
    assert concept.name_zh == char
    assert concept.fact_ref.collection == "earthly_branches"
    assert concept.fact_ref.id == branch_id
    assert f"第 {order} 位" in concept.short_definition
    assert classification in concept.short_definition
    assert "不同的實體" in concept.plain_explanation
    assert concept.traditional_associations == ()
    assert concept.source_status.value == "requires_validation"
    assert "branch_polarity" in concept.source_ids


def test_existing_id_meanings_are_preserved():
    kb = KnowledgeBase()
    assert kb.get_concept("yin") == kb.get_concept("陰")
    assert kb.get_concept("wu") == kb.get_concept("戊")
    assert kb.get_concept("branch_yin") == kb.get_concept("寅")
    assert kb.get_concept("branch_wu") == kb.get_concept("午")
    assert kb.get_concept("earthly_branches").name_zh == "地支"
    for stem in kb.data.heavenly_stems:
        assert kb.get_concept(stem.id) == kb.get_concept(stem.char)
    with pytest.raises(KeyError):
        kb.get_concept("branch_missing")


def test_every_stored_fact_reference_resolves():
    kb = KnowledgeBase()
    for concept in kb.concepts.concepts:
        if concept.fact_ref:
            ref = concept.fact_ref
            assert any(fact.id == ref.id for fact in getattr(kb.data, ref.collection))


def test_branch_yaml_contains_references_not_classification_values():
    path = Path(__file__).resolve().parents[1] / "knowledge/concepts/earthly_branches.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    branches = [c for c in raw["concepts"] if c.get("fact_ref")]
    assert len(branches) == 12
    for concept in branches:
        assert not {"order", "element", "yin_yang"} & concept.keys()
        # Classification is absent even from stored prose; it is joined at query time.
        text = concept["short_definition"] + concept["plain_explanation"]
        assert not any(term in text for term in ("陽木", "陰木", "陽水", "陰水", "第 3 位"))


def test_branch_explanation_follows_all_basic_attributes_and_keeps_yaml_prose(knowledge_dir):
    path = knowledge_dir / "地支/earthly_branches.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    yin, mao = raw["earthly_branches"][2:4]
    # Synthetic data only: catches a second classification table or stale prose.
    yin["order"], mao["order"] = mao["order"], yin["order"]
    yin["element"], yin["yin_yang"] = "water", "yin"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    path = knowledge_dir / "concepts/earthly_branches.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    entry = next(c for c in raw["concepts"] if c["id"] == "branch_yin")
    entry["plain_explanation"] = "這是測試資料的說明。"
    entry["source_status"] = {"value": "requires_validation", "note": "測試：等待版本核對。"}
    entry["source_ids"] = ["concept_spec"]
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(knowledge_dir)
    concept = kb.get_concept("寅")
    assert "第 4 位" in concept.short_definition and "陰水" in concept.short_definition
    assert "陰是它的陰陽分類，水是它的五行分類" in concept.plain_explanation
    assert "這是測試資料的說明。" in concept.plain_explanation
    assert concept.source_ids == ("concept_spec",)
    assert concept.source_status.note == "測試：等待版本核對。"
    stored = next(c for c in kb.concepts.concepts if c.id == "branch_yin")
    assert concept.source_status == stored.source_status
    assert stored.plain_explanation == "這是測試資料的說明。"
    assert kb.get_concept("寅") == concept  # No repeated appending to stored text.
    assert "陽木" in get_concept("寅").short_definition


@pytest.mark.parametrize("mutation", [
    "missing", "missing_ref", "unknown_ref", "duplicate_ref", "mismatched_name", "unknown_source",
])
def test_loader_rejects_incomplete_or_inconsistent_branch_concepts(knowledge_dir, mutation):
    path = knowledge_dir / "concepts/earthly_branches.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    entry = next(c for c in raw["concepts"] if c["id"] == "branch_yin")
    if mutation == "missing":
        raw["concepts"].remove(entry)
    elif mutation == "missing_ref":
        entry.pop("fact_ref")
    elif mutation == "unknown_ref":
        entry["fact_ref"]["id"] = "missing"
    elif mutation == "duplicate_ref":
        entry["fact_ref"]["id"] = "zi"
    elif mutation == "mismatched_name":
        entry["name_zh"] = "錯"
    else:
        entry["source_ids"] = ["missing"]
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError):
        load_concepts(knowledge_dir)


@pytest.mark.parametrize("field", [
    "personality", "career", "wealth", "marriage", "health_prediction", "fortune", "luck",
    "auspicious", "inauspicious", "身強", "身弱", "喜用神", "格局", "大運", "流年",
    "order", "yin_yang", "element",
])
def test_layer1_concepts_reject_interpretation_and_duplicate_attribute_fields(field):
    kb = KnowledgeBase()
    for key in ("陰", "木", "甲", "寅"):
        raw = kb.get_concept(key).model_dump()
        with pytest.raises(ValidationError, match="Extra inputs"):
            Concept.model_validate({**raw, field: "unsupported"})


def test_curated_layer1_text_stays_within_scope():
    # Dataset regression check, not a general semantic classifier.
    kb = KnowledgeBase()
    for char in "陰陽木火土金水甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥":
        concept = kb.get_concept(char)
        text = concept.short_definition + concept.plain_explanation + "".join(concept.notes)
        assert not any(term in text for term in (
            "身強", "身弱", "喜用神", "格局", "大運", "流年", "你會", "此人", "財運亨通", "容易患",
        ))
    for branch in kb.data.earthly_branches:
        concept = kb.get_concept(branch.char)
        text = concept.short_definition + concept.plain_explanation
        assert not any(term in text for term in (
            "藏干", "三合", "六合", "六沖", "旺衰", "月份", "月令", "時辰", "方位",
            "老鼠", "老虎", "兔", "馬", "北方", "南方", "正月", "二月", "23:00",
        ))
    assert kb.get_concept("stem_imagery").source_status.value == "requires_validation"
