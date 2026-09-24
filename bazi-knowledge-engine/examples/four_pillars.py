"""Structural analysis of caller-supplied pillars; use --json to inspect the full trace."""

import argparse

from bazi_knowledge import KnowledgeBase


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete structured result")
    args = parser.parse_args()
    result = KnowledgeBase().analyze_four_pillars(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
    if args.json:
        print(result.model_dump_json(indent=2))
        return
    print(f"Day Master: {result.day_master.char}")
    for item in result.pillars:
        visible = item.visible_stem_analysis
        label = "日主" if visible.role == "day_master" else visible.ten_god_result.ten_god.name_zh
        print(f"\n{item.position.title()}:")
        print(f"{visible.stem.char} → {label}")
        print(f"{item.pillar.branch.char}:")
        for hidden in item.branch_analysis.hidden_stem_results:
            print(f"  {hidden.hidden_stem.char} → {hidden.ten_god_result.ten_god.name_zh}")


if __name__ == "__main__":
    main()
