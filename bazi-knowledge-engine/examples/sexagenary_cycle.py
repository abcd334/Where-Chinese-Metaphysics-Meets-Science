"""Show the derived 60-pillar cycle and its validation API."""

from bazi_knowledge import KnowledgeBase


def main():
    kb = KnowledgeBase()
    for index, pillar in enumerate(kb.generate_sexagenary_cycle(), start=1):
        print(f"{index:2}: {pillar.stem.char}{pillar.branch.char}")
    for value in ("甲子", "甲丑", "癸亥"):
        print(f"{value}: valid={kb.is_valid_pillar(value)}")
    print(f"癸亥 index: {kb.get_sexagenary_index('癸亥')}")
    try:
        kb.analyze_four_pillars(year="甲丑", month="辛卯", day="壬戌", hour="乙巳")
    except ValueError as error:
        print(error)


if __name__ == "__main__":
    main()
