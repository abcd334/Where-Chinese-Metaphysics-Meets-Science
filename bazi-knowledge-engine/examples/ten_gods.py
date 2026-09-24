"""Show two stem-only Ten Gods results and their structured reasoning traces."""

import json

from bazi_knowledge import KnowledgeBase


def main():
    kb = KnowledgeBase()
    for target in ("乙", "辛"):
        result = kb.get_ten_god("壬", target)
        print(f"壬 + {target} → {result.ten_god.name_zh}")
        for step in result.trace:
            print(f"  {step.step}: {step.result}")
        print(json.dumps(result.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
