from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import ConceptData, KnowledgeBase, get_concept, load_concepts


@pytest.fixture
def knowledge_dir(tmp_path):
    return Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))


@pytest.mark.parametrize("key,name", [
    ("wood", "木"), ("fire", "火"), ("earth", "土"), ("metal", "金"), ("water", "水"),
    ("yin", "陰"), ("yang", "陽"), ("yin_yang", "陰陽"), ("five_elements", "五行"),
    ("generates", "相生"), ("controls", "相剋"), ("heavenly_stems", "天干"),
    ("earthly_branches", "地支"), ("hidden_stems", "藏干"),
    ("hidden_stems_seasons", "藏干與四季"),
])
def test_concept_lookup_by_id_and_name(key, name):
    kb = KnowledgeBase()
    concept = kb.get_concept(key)
    assert concept.name_zh == name
    assert concept is kb.get_concept(name)
    assert concept.short_definition.strip()
    assert concept.plain_explanation.strip()
    assert concept.source_status.note.strip()
    assert concept.source_ids


@pytest.mark.parametrize("element", ["wood", "fire", "earth", "metal", "water"])
def test_elements_have_distinct_sourced_association_kinds(element):
    concept = get_concept(element)
    assert concept.fact_ref.collection == "elements"
    assert concept.fact_ref.id == element
    assert {a.kind for a in concept.traditional_associations} == {"symbol", "season", "direction"}
    assert all(a.value and a.scope and a.source_ids and a.source_status.note
               for a in concept.traditional_associations)


def test_all_stem_explanations_are_resolved_from_facts():
    kb = KnowledgeBase()
    for stem in kb.data.heavenly_stems:
        concept = kb.get_concept(stem.char)
        assert concept == kb.get_concept(stem.id)
        assert concept.fact_ref.id == stem.id
        assert concept.source_status.value == "derived_from_facts"
        assert str(stem.order) in concept.short_definition
        assert not concept.traditional_associations
    assert "陽木" in kb.get_concept("甲").short_definition


def test_stem_explanation_follows_custom_fact_data(knowledge_dir):
    path = knowledge_dir / "天干" / "heavenly_stems.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Synthetic fixture: a cached or hard-coded explanation must not mask loaded facts.
    raw["heavenly_stems"][0]["element"] = "water"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    assert "陽水" in KnowledgeBase(knowledge_dir).get_concept("甲").short_definition
    assert "陽木" in get_concept("甲").short_definition


def test_facts_remain_usable_without_concept_directory(knowledge_dir):
    # Rename within the fixture instead of deleting the actual project data.
    (knowledge_dir / "concepts").rename(knowledge_dir / "concepts_unused")
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_heavenly_stem("甲").model_dump() == {
        "id": "jia", "char": "甲", "order": 1, "yin_yang": "yang", "element": "wood",
    }
    assert [stem.char for stem in kb.get_hidden_stems("寅")] == ["甲", "丙", "戊"]
    with pytest.raises(FileNotFoundError):
        kb.get_concept("木")


def test_relative_custom_directory_stays_stable_for_lazy_loading(knowledge_dir, monkeypatch):
    monkeypatch.chdir(knowledge_dir.parent)
    kb = KnowledgeBase("knowledge")
    monkeypatch.chdir(knowledge_dir)
    assert kb.get_concept("木").id == "wood"


def test_all_source_references_resolve():
    data = load_concepts()
    sources = {source.id: source for source in data.sources}
    for concept in data.concepts:
        for source_id in concept.source_ids:
            assert sources[source_id].locator and sources[source_id].scope
        for association in concept.traditional_associations:
            assert set(association.source_ids) <= sources.keys()


@pytest.mark.parametrize("field", ["short_definition", "plain_explanation"])
@pytest.mark.parametrize("bad_value", ["", "   ", None])
def test_concepts_require_nonempty_explanations(field, bad_value):
    raw = load_concepts().model_dump(mode="json")
    raw["concepts"][0][field] = bad_value
    with pytest.raises(ValidationError):
        ConceptData.model_validate(raw)


@pytest.mark.parametrize("mutation", [
    "duplicate_id", "duplicate_name", "unknown_source", "unknown_association_source",
    "unknown_fact", "duplicate_fact", "missing_element", "missing_overview", "invalid_status",
])
def test_invalid_concepts_are_rejected(mutation):
    kb = KnowledgeBase()
    raw = kb.concepts.model_dump(mode="json")
    wood = next(c for c in raw["concepts"] if c["id"] == "wood")
    if mutation == "duplicate_id":
        raw["concepts"][1]["id"] = raw["concepts"][0]["id"]
    elif mutation == "duplicate_name":
        raw["concepts"][1]["name_zh"] = raw["concepts"][0]["name_zh"]
    elif mutation == "unknown_source":
        wood["source_ids"] = ["missing"]
    elif mutation == "unknown_association_source":
        wood["traditional_associations"][0]["source_ids"] = ["missing"]
    elif mutation == "unknown_fact":
        wood["fact_ref"]["id"] = "missing"
    elif mutation == "duplicate_fact":
        next(c for c in raw["concepts"] if c["id"] == "fire")["fact_ref"] = wood["fact_ref"]
    elif mutation == "missing_element":
        raw["concepts"].remove(wood)
    elif mutation == "missing_overview":
        raw["concepts"] = [c for c in raw["concepts"] if c["id"] != "heavenly_stems"]
    else:
        wood["source_status"]["value"] = "scientific_law"
    with pytest.raises(ValueError):
        ConceptData.model_validate(raw).validate_against(kb.data)


@pytest.mark.parametrize("field", ["personality", "fortune", "career", "marriage", "health_prediction"])
def test_interpretation_fields_are_rejected_in_both_layers(field):
    kb = KnowledgeBase()
    fact = kb.get_heavenly_stem("甲")
    concept = kb.get_concept("wood")
    for record in (fact, concept):
        with pytest.raises(ValidationError, match="Extra inputs"):
            type(record).model_validate({**record.model_dump(), field: "unsupported"})


def test_concept_text_has_no_personal_prediction_templates():
    # A regression guard for this curated dataset, not a semantic safety classifier.
    texts = []
    for concept in load_concepts().concepts:
        texts.extend([concept.short_definition, concept.plain_explanation])
        texts.extend(a.value for a in concept.traditional_associations)
    assert not any(term in text for text in texts for term in
                   ("你會", "此人", "的人", "財運亨通", "婚姻美滿", "必定成功", "容易患"))


@pytest.mark.parametrize("content,error", [
    ("concepts: {}", ValueError),
    ("concepts: []\nconcepts: []", ValueError),
    ("concepts: [", yaml.YAMLError),
    ("concepts: []\nextra: true", ValidationError),
])
def test_concept_yaml_uses_existing_strict_loader(knowledge_dir, content, error):
    (knowledge_dir / "concepts" / "yin_yang.yaml").write_text(content, encoding="utf-8")
    with pytest.raises(error):
        KnowledgeBase(knowledge_dir).get_concept("木")


def test_unknown_concept_raises_key_error():
    with pytest.raises(KeyError, match="Unknown concept"):
        get_concept("missing")


def test_pending_imagery_is_separate_from_stem_definitions():
    pending = get_concept("stem_imagery")
    assert pending.source_status.value == "requires_validation"
    assert pending.traditional_associations == ()
    assert get_concept("甲").traditional_associations == ()


def test_source_ids_and_urls_are_validated():
    raw = load_concepts().model_dump(mode="json")
    raw["sources"][1]["id"] = raw["sources"][0]["id"]
    with pytest.raises(ValidationError, match="duplicate id"):
        ConceptData.model_validate(raw)
    raw = load_concepts().model_dump(mode="json")
    raw["sources"][0]["url"] = "not-a-url"
    with pytest.raises(ValidationError):
        ConceptData.model_validate(raw)
