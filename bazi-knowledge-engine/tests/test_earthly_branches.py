import pytest

from bazi_knowledge import get_earthly_branch, load_knowledge


@pytest.mark.parametrize("char,order,yin_yang,element", [
    ("子", 1, "yang", "water"),
    ("丑", 2, "yin", "earth"),
    ("寅", 3, "yang", "wood"),
    ("卯", 4, "yin", "wood"),
    ("辰", 5, "yang", "earth"),
    ("巳", 6, "yin", "fire"),
    ("午", 7, "yang", "fire"),
    ("未", 8, "yin", "earth"),
    ("申", 9, "yang", "metal"),
    ("酉", 10, "yin", "metal"),
    ("戌", 11, "yang", "earth"),
    ("亥", 12, "yin", "water"),
])
def test_earthly_branch_attributes(char, order, yin_yang, element):
    branch = get_earthly_branch(char)
    assert (branch.char, branch.order, branch.yin_yang, branch.element) == (
        char, order, yin_yang, element,
    )


def test_all_twelve_branches_and_unique_orders():
    records = load_knowledge().earthly_branches
    assert len(records) == 12
    assert {record.char for record in records} == set("子丑寅卯辰巳午未申酉戌亥")
    assert {record.order for record in records} == set(range(1, 13))
    assert len({record.id for record in records}) == 12
