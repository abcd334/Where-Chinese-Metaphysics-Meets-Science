from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import KnowledgeBase, KnowledgeData, load_knowledge


@pytest.fixture
def knowledge_dir(tmp_path):
    source = Path(__file__).resolve().parents[1] / "knowledge"
    return Path(copytree(source, tmp_path / "knowledge"))


@pytest.mark.parametrize("collection", ["elements", "heavenly_stems", "earthly_branches"])
def test_reject_duplicate_orders(collection):
    raw = load_knowledge().model_dump(mode="json")
    raw[collection][1]["order"] = raw[collection][0]["order"]
    with pytest.raises(ValidationError, match="order must be unique"):
        KnowledgeData.model_validate(raw)


@pytest.mark.parametrize("collection,field", [
    ("yin_yang", "id"), ("yin_yang", "name_zh"), ("elements", "id"),
    ("elements", "name_zh"), ("heavenly_stems", "id"),
    ("heavenly_stems", "char"), ("earthly_branches", "id"), ("earthly_branches", "char"),
])
def test_reject_duplicate_identifiers_and_labels(collection, field):
    raw = load_knowledge().model_dump(mode="json")
    raw[collection][1][field] = raw[collection][0][field]
    with pytest.raises(ValidationError, match=f"duplicate {field}"):
        KnowledgeData.model_validate(raw)


@pytest.mark.parametrize("collection,field,value", [
    ("heavenly_stems", "element", "unknown"),
    ("earthly_branches", "yin_yang", "unknown"),
    ("relations", "source", "unknown"),
    ("relations", "target", "unknown"),
    ("relations", "relation", "indirect"),
    ("earthly_branches", "unsupported_field", "not allowed"),
    ("elements", "order", True),
    ("elements", "order", "1"),
    ("elements", "order", 1.0),
    ("elements", "order", 0),
])
def test_reject_invalid_fields(collection, field, value):
    raw = load_knowledge().model_dump(mode="json")
    raw[collection][0][field] = value
    with pytest.raises(ValidationError):
        KnowledgeData.model_validate(raw)


@pytest.mark.parametrize("collection", [
    "yin_yang", "elements", "heavenly_stems", "earthly_branches", "relations",
])
def test_reject_incomplete_collections(collection):
    raw = load_knowledge().model_dump(mode="json")
    raw[collection].pop()
    with pytest.raises(ValidationError):
        KnowledgeData.model_validate(raw)


@pytest.mark.parametrize("mutation", ["duplicate", "conflict", "self", "missing_source"])
def test_reject_invalid_relations(mutation):
    raw = load_knowledge().model_dump(mode="json")
    edges = raw["relations"]
    if mutation == "duplicate":
        edges[1] = edges[0].copy()
    elif mutation == "conflict":
        edges[5] = {**edges[0], "relation": "controls"}
    elif mutation == "self":
        edges[0]["target"] = edges[0]["source"]
    else:
        edges[0]["source"] = "metal"
    with pytest.raises(ValidationError):
        KnowledgeData.model_validate(raw)


def test_relations_are_loaded_from_yaml(knowledge_dir):
    path = knowledge_dir / "五行" / "five_elements.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Synthetic fixture, not canonical knowledge: exchange the two edge labels.
    for edge in document["relations"]:
        edge["relation"] = "controls" if edge["relation"] == "generates" else "generates"
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_generating_element("水") == "火"
    assert kb.get_controlling_element("水") == "木"
    assert kb.get_element_relation("水", "木") == "controls"
    assert KnowledgeBase().get_generating_element("水") == "木"


def test_default_loader_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert KnowledgeBase().get_heavenly_stem("壬").order == 9


@pytest.mark.parametrize("method,args", [
    ("get_heavenly_stem", ("錯",)),
    ("get_earthly_branch", ("錯",)),
    ("get_generating_element", ("錯",)),
    ("get_controlling_element", ("錯",)),
    ("get_element_relation", ("錯", "木")),
    ("get_element_relation", ("水", "錯")),
])
def test_unknown_input_raises_key_error(method, args):
    with pytest.raises(KeyError):
        getattr(KnowledgeBase(), method)(*args)


def test_missing_file_is_reported(knowledge_dir):
    (knowledge_dir / "陰陽" / "yin_yang.yaml").unlink()
    with pytest.raises(FileNotFoundError):
        load_knowledge(knowledge_dir)


@pytest.mark.parametrize("text,error,match", [
    ("yin_yang: []\nyin_yang: []\n", ValueError, "Duplicate YAML key"),
    ("yin_yang:\n  - {id: yin, id: yang, name_zh: 陰}\n", ValueError, "Duplicate YAML key"),
    ("[]", ValueError, "expected a YAML mapping"),
    ("yin_yang: [", yaml.YAMLError, None),
    ("!!python/object/apply:builtins.eval ['1 + 1']", yaml.YAMLError, None),
])
def test_invalid_yaml_is_rejected(knowledge_dir, text, error, match):
    (knowledge_dir / "陰陽" / "yin_yang.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(error, match=match):
        load_knowledge(knowledge_dir)


def test_duplicate_collections_across_files_are_rejected(knowledge_dir):
    path = knowledge_dir / "五行" / "five_elements.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nyin_yang: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate top-level collection"):
        load_knowledge(knowledge_dir)
