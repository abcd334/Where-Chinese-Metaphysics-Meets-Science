from pathlib import Path
from shutil import copytree

import pytest
import yaml
from pydantic import ValidationError

from bazi_knowledge import HeavenlyStem, KnowledgeBase, get_hidden_stems, load_knowledge


CANONICAL = [
    ("子", "zi", ["癸"], ["gui"]),
    ("丑", "chou", ["己", "癸", "辛"], ["ji", "gui", "xin"]),
    ("寅", "yin", ["甲", "丙", "戊"], ["jia", "bing", "wu"]),
    ("卯", "mao", ["乙"], ["yi"]),
    ("辰", "chen", ["戊", "乙", "癸"], ["wu", "yi", "gui"]),
    ("巳", "si", ["丙", "戊", "庚"], ["bing", "wu", "geng"]),
    ("午", "wu", ["丁", "己"], ["ding", "ji"]),
    ("未", "wei", ["己", "丁", "乙"], ["ji", "ding", "yi"]),
    ("申", "shen", ["庚", "壬", "戊"], ["geng", "ren", "wu"]),
    ("酉", "you", ["辛"], ["xin"]),
    ("戌", "xu", ["戊", "辛", "丁"], ["wu", "xin", "ding"]),
    ("亥", "hai", ["壬", "甲"], ["ren", "jia"]),
]


@pytest.mark.parametrize("char,branch_id,chars,stem_ids", CANONICAL)
@pytest.mark.parametrize("use_id", [False, True], ids=["character", "branch_id"])
def test_canonical_hidden_stems(char, branch_id, chars, stem_ids, use_id):
    stems = get_hidden_stems(branch_id if use_id else char)
    assert isinstance(stems, list)
    assert all(isinstance(stem, HeavenlyStem) for stem in stems)
    assert [stem.char for stem in stems] == chars
    assert [stem.id for stem in stems] == stem_ids


def test_all_branches_are_covered_and_references_resolve_to_existing_objects():
    kb = KnowledgeBase()
    assert len(kb.data.hidden_stems) == 12
    assert {record.branch_id for record in kb.data.hidden_stems} == {
        record.id for record in kb.data.earthly_branches
    }
    stems_by_id = {stem.id: stem for stem in kb.data.heavenly_stems}
    for hidden in kb.data.hidden_stems:
        resolved = kb.get_hidden_stems(hidden.branch_id)
        assert len(resolved) == len(hidden.stem_ids)
        for stem_id, stem in zip(hidden.stem_ids, resolved, strict=True):
            assert stem is stems_by_id[stem_id]


def test_xu_attributes_come_from_basic_data():
    kb = KnowledgeBase()
    stems = kb.get_hidden_stems("戌")
    assert [(stem.char, stem.yin_yang, stem.element) for stem in stems] == [
        ("戊", "yang", "earth"), ("辛", "yin", "metal"), ("丁", "yin", "fire"),
    ]
    assert all(stem is kb.get_heavenly_stem(stem.char) for stem in stems)


@pytest.fixture
def knowledge_dir(tmp_path):
    source = Path(__file__).resolve().parents[1] / "knowledge"
    return Path(copytree(source, tmp_path / "knowledge"))


@pytest.mark.parametrize("mutation,match", [
    ("missing_mapping", "at least 12"),
    ("extra_mapping", "at most 12"),
    ("unknown_branch", "unknown branch reference"),
    ("duplicate_branch", "duplicate branch reference"),
    ("unknown_stem", "unknown stem reference"),
    ("duplicate_stem", "duplicate stem reference"),
    ("empty_stems", "at least 1"),
    ("duplicated_attributes", "valid string"),
    ("extra_field", "Extra inputs are not permitted"),
    ("missing_collection", "Field required"),
])
def test_loader_rejects_invalid_hidden_stems(knowledge_dir, mutation, match):
    path = knowledge_dir / "hidden_stems.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    records = document["hidden_stems"]
    if mutation == "missing_mapping":
        records.pop()
    elif mutation == "extra_mapping":
        records.append(records[0].copy())
    elif mutation == "unknown_branch":
        records[0]["branch_id"] = "unknown"
    elif mutation == "duplicate_branch":
        records[1]["branch_id"] = records[0]["branch_id"]
    elif mutation == "unknown_stem":
        records[0]["stem_ids"] = ["unknown"]
    elif mutation == "duplicate_stem":
        records[0]["stem_ids"] = ["gui", "gui"]
    elif mutation == "empty_stems":
        records[0]["stem_ids"] = []
    elif mutation == "duplicated_attributes":
        records[0]["stem_ids"] = [{"id": "gui", "element": "water"}]
    elif mutation == "extra_field":
        records[0]["element"] = "water"
    else:
        document.pop("hidden_stems")
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValidationError, match=match):
        load_knowledge(knowledge_dir)


def test_resolution_uses_current_heavenly_stem_yaml(knowledge_dir):
    path = knowledge_dir / "天干" / "heavenly_stems.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Synthetic fixture only: verify hidden stems resolve the loaded basic data.
    xin = next(stem for stem in document["heavenly_stems"] if stem["id"] == "xin")
    xin["element"] = "wood"
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(knowledge_dir)
    assert kb.get_hidden_stems("戌")[1] is kb.get_heavenly_stem("辛")
    assert kb.get_hidden_stems("戌")[1].element == "wood"
    assert get_hidden_stems("戌")[1].element == "metal"


def test_order_comes_from_hidden_stem_yaml(knowledge_dir):
    path = knowledge_dir / "hidden_stems.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    # Synthetic fixture only: no sorting by heavenly-stem order is allowed.
    hidden = next(record for record in document["hidden_stems"] if record["branch_id"] == "yin")
    hidden["stem_ids"] = ["wu", "bing", "jia"]
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    assert [stem.id for stem in KnowledgeBase(knowledge_dir).get_hidden_stems("寅")] == [
        "wu", "bing", "jia",
    ]


@pytest.mark.parametrize("branch", ["錯", "unknown", "", "甲", "jia"])
def test_unknown_branch_raises_key_error(branch):
    with pytest.raises(KeyError, match="Unknown earthly branch"):
        get_hidden_stems(branch)


def test_returned_list_does_not_change_stored_references():
    kb = KnowledgeBase()
    kb.get_hidden_stems("寅").clear()
    assert [stem.id for stem in kb.get_hidden_stems("寅")] == ["jia", "bing", "wu"]


def test_missing_hidden_stems_file_is_reported(knowledge_dir):
    (knowledge_dir / "hidden_stems.yaml").unlink()
    with pytest.raises(FileNotFoundError):
        load_knowledge(knowledge_dir)
