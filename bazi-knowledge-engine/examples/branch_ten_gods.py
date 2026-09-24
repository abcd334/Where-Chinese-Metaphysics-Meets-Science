"""Run with: python examples/branch_ten_gods.py (after installing the package)."""

from bazi_knowledge import KnowledgeBase


def main():
    kb = KnowledgeBase()
    result = kb.get_branch_ten_gods("壬", "戌")
    print(f"日主：{result.day_master.char}；地支：{result.branch.char}")
    for step in result.trace:
        print(f"{step.operation}: {', '.join(step.input_refs)} → {', '.join(step.output_refs)}")
        print(f"  source_ids: {', '.join(step.source_ids)}")
    for item in result.hidden_stem_results:
        nested = item.ten_god_result
        print(f"{item.hidden_stem.char} → {nested.ten_god.name_zh}")
        for step in nested.trace:
            print(f"  {step.step}: {step.result}")
        print(f"  rule_id: {nested.ten_god.id}; status: {nested.ten_god.source_status.value}")
    print(f"藏干來源狀態：{result.hidden_stem_source_status.value}")
    for source in result.sources:
        print(f"{source.id}: {source.locator}")


if __name__ == "__main__":
    main()
