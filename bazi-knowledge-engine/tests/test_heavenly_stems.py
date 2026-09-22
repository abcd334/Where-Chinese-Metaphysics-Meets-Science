import pytest

from bazi_knowledge import get_heavenly_stem, load_knowledge


@pytest.mark.parametrize("char,order,yin_yang,element", [
    ("甲", 1, "yang", "wood"),
    ("乙", 2, "yin", "wood"),
    ("丙", 3, "yang", "fire"),
    ("丁", 4, "yin", "fire"),
    ("戊", 5, "yang", "earth"),
    ("己", 6, "yin", "earth"),
    ("庚", 7, "yang", "metal"),
    ("辛", 8, "yin", "metal"),
    ("壬", 9, "yang", "water"),
    ("癸", 10, "yin", "water"),
])
def test_heavenly_stem_attributes(char, order, yin_yang, element):
    stem = get_heavenly_stem(char)
    assert (stem.char, stem.order, stem.yin_yang, stem.element) == (
        char, order, yin_yang, element,
    )


def test_all_ten_stems_and_unique_orders():
    records = load_knowledge().heavenly_stems
    assert len(records) == 10
    assert {record.char for record in records} == set("甲乙丙丁戊己庚辛壬癸")
    assert {record.order for record in records} == set(range(1, 11))
    assert len({record.id for record in records}) == 10
