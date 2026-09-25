"""Query fixed pairs only; no Four Pillars scan or interpretation."""

from bazi_knowledge import KnowledgeBase


def main():
    kb = KnowledgeBase()
    for method, first, second in (
        (kb.get_stem_relations, "丙", "辛"),
        (kb.get_branch_relations, "卯", "戌"),
        (kb.get_branch_relations, "辰", "戌"),
        (kb.get_branch_relations, "寅", "卯"),
    ):
        results = method(first, second)
        print(f"{first} + {second}: {[result.rule.relation for result in results]}")
        for result in results:
            print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
