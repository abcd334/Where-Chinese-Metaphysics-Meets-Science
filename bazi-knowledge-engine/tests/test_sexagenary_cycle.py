"""The cycle follows stored order, not a hard-coded pair or polarity table."""

from collections import Counter
from itertools import product
from pathlib import Path
from shutil import copytree

import pytest
import yaml

from bazi_knowledge import KnowledgeBase, Pillar, generate_sexagenary_cycle, get_sexagenary_index, is_valid_pillar


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase()


def chars(pillar):
    return pillar.stem.char + pillar.branch.char


def test_cycle_is_complete_unique_and_reuses_basic_objects(kb):
    cycle = kb.generate_sexagenary_cycle()
    assert isinstance(cycle, tuple) and len(cycle) == 60
    assert len({chars(pillar) for pillar in cycle}) == 60
    assert Counter(p.stem.id for p in cycle) == Counter({s.id: 6 for s in kb.data.heavenly_stems})
    assert Counter(p.branch.id for p in cycle) == Counter({b.id: 5 for b in kb.data.earthly_branches})
    for index, pillar in enumerate(cycle, start=1):
        assert isinstance(pillar, Pillar)
        assert pillar.stem is kb.get_heavenly_stem(pillar.stem.char)
        assert pillar.branch is kb.get_earthly_branch(pillar.branch.char)
        assert kb.get_sexagenary_index(chars(pillar)) == index
        assert kb.is_valid_pillar(chars(pillar)) is True
    for current, following in zip(cycle, (*cycle[1:], cycle[0]), strict=True):
        assert following.stem.order == current.stem.order % 10 + 1
        assert following.branch.order == current.branch.order % 12 + 1


@pytest.mark.parametrize("pillar,index", [
    ("甲子", 1), ("乙丑", 2), ("丙寅", 3), ("丁卯", 4),
    ("癸酉", 10), ("甲戌", 11), ("乙亥", 12), ("丙子", 13),
    ("辛卯", 28), ("壬戌", 59), ("癸亥", 60),
])
def test_known_positions(kb, pillar, index):
    assert kb.get_sexagenary_index(pillar) == index


@pytest.mark.parametrize("stem,branch", tuple(product("甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥")))
def test_all_120_pairs_have_exactly_the_allowed_60(kb, stem, branch):
    # Independent invariant of simultaneous 10/12 position cycles (not yin_yang fields).
    expected = kb.get_heavenly_stem(stem).order % 2 == kb.get_earthly_branch(branch).order % 2
    assert kb.is_valid_pillar(stem + branch) is expected
    if not expected:
        with pytest.raises(ValueError):
            kb.get_sexagenary_index(stem + branch)


@pytest.mark.parametrize("invalid", ["甲丑", "乙子", "丙卯", "乙寅", "丙", "寅", "ABC", "甲甲", "子甲", "", "jiazi", "甲子 ", " 甲子", "2026-09-25"])
def test_invalid_strings(kb, invalid):
    assert kb.is_valid_pillar(invalid) is False
    with pytest.raises(ValueError):
        kb.get_sexagenary_index(invalid)


@pytest.mark.parametrize("invalid", [None, 1, True, ["甲", "子"], {"stem": "甲", "branch": "子"}])
def test_wrong_types_raise_type_error(kb, invalid):
    with pytest.raises(TypeError):
        kb.is_valid_pillar(invalid)
    with pytest.raises(TypeError):
        kb.get_sexagenary_index(invalid)


@pytest.mark.parametrize("position", ["year", "month", "day", "hour"])
@pytest.mark.parametrize("invalid", ["甲丑", "乙子", "丙卯"])
def test_four_pillars_reject_invalid_pairs_before_analysis(monkeypatch, position, invalid):
    kb = KnowledgeBase()

    def unexpected(*args):
        pytest.fail("Layer 2 must not run before all pillars pass cycle validation")

    monkeypatch.setattr(kb, "get_ten_god", unexpected)
    monkeypatch.setattr(kb, "get_branch_ten_gods", unexpected)
    chart = dict(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
    chart[position] = invalid
    with pytest.raises(ValueError, match=f"{position}: invalid sexagenary pillar"):
        kb.analyze_four_pillars(**chart)


def test_all_60_pillars_are_accepted_in_each_chart_position(kb):
    for pillar in kb.generate_sexagenary_cycle():
        text = chars(pillar)
        result = kb.analyze_four_pillars(year=text, month=text, day=text, hour=text)
        assert result.day_master is pillar.stem
        assert all(item.pillar == pillar for item in result.pillars)
        for step in result.trace[1:5]:
            assert step.output_refs[-1] == f"sexagenary_cycle:{kb.get_sexagenary_index(text)}"


@pytest.mark.parametrize("collection,path", [
    ("heavenly_stems", "天干/heavenly_stems.yaml"),
    ("earthly_branches", "地支/earthly_branches.yaml"),
])
def test_cycle_follows_order_values_not_yaml_list_position(tmp_path, collection, path):
    root = Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))
    file = root / path
    raw = yaml.safe_load(file.read_text(encoding="utf-8"))
    raw[collection].reverse()
    file.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    assert KnowledgeBase(root).generate_sexagenary_cycle() == generate_sexagenary_cycle()
    # Synthetic order changes establish that no canonical pair table or polarity shortcut is used.
    records = sorted(raw[collection], key=lambda record: record["order"])
    records[0]["order"], records[1]["order"] = records[1]["order"], records[0]["order"]
    file.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    kb = KnowledgeBase(root)
    expected_first = "乙子" if collection == "heavenly_stems" else "甲丑"
    assert chars(kb.generate_sexagenary_cycle()[0]) == expected_first
    assert kb.get_sexagenary_index(expected_first) == 1
    assert kb.is_valid_pillar("甲子") is False


def test_module_wrappers_and_fact_only_loading(tmp_path):
    assert is_valid_pillar("甲子") is True
    assert is_valid_pillar("甲丑") is False
    assert get_sexagenary_index("癸亥") == 60
    root = Path(copytree(Path(__file__).resolve().parents[1] / "knowledge", tmp_path / "knowledge"))
    (root / "concepts").rename(root / "unused_concepts")
    (root / "ten_gods.yaml").rename(root / "unused_ten_gods.yaml")
    kb = KnowledgeBase(root)
    assert kb.generate_sexagenary_cycle() == generate_sexagenary_cycle()
    assert kb.is_valid_pillar("丙寅") is True
    assert kb.get_sexagenary_index("丙寅") == 3
