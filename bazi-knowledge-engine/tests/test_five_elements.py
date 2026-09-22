import pytest

from bazi_knowledge import (
    KnowledgeBase,
    get_controlling_element,
    get_element_relation,
    get_generating_element,
    load_knowledge,
)

GENERATES = [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]
CONTROLS = [("木", "土"), ("土", "水"), ("水", "火"), ("火", "金"), ("金", "木")]


def test_yin_yang_and_all_five_elements():
    data = load_knowledge()
    assert {(record.id, record.name_zh) for record in data.yin_yang} == {
        ("yin", "陰"), ("yang", "陽"),
    }
    assert {(record.id, record.name_zh, record.order) for record in data.elements} == {
        ("wood", "木", 1), ("fire", "火", 2), ("earth", "土", 3),
        ("metal", "金", 4), ("water", "水", 5),
    }
    assert len(data.elements) == 5
    assert len({record.order for record in data.elements}) == 5


@pytest.mark.parametrize("source,target", GENERATES)
def test_generating_elements(source, target):
    assert get_generating_element(source) == target
    assert get_element_relation(source, target) == "generates"


@pytest.mark.parametrize("source,target", CONTROLS)
def test_controlling_elements(source, target):
    assert get_controlling_element(source) == target
    assert get_element_relation(source, target) == "controls"


@pytest.mark.parametrize("source", "木火土金水")
@pytest.mark.parametrize("target", "木火土金水")
def test_only_direct_relations(source, target):
    expected = {(a, b): "generates" for a, b in GENERATES}
    expected.update({(a, b): "controls" for a, b in CONTROLS})
    assert KnowledgeBase().get_element_relation(source, target) == expected.get((source, target))
