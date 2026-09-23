"""Print complete fact/concept examples and the seasonal reference trace."""

import json

from bazi_knowledge import KnowledgeBase


def main():
    kb = KnowledgeBase()
    wood = next(element for element in kb.data.elements if element.id == "wood")
    tree = {
        element.name_zh: [stem.model_dump() for stem in kb.data.heavenly_stems
                         if stem.element == element.id]
        for element in kb.data.elements
    }
    print(json.dumps({
        "wood": {"fact": wood.model_dump(), "concept": kb.get_concept("木").model_dump(mode="json")},
        "jia": {"fact": kb.get_heavenly_stem("甲").model_dump(),
                "concept": kb.get_concept("甲").model_dump(mode="json")},
        "stems_by_element": tree,
        "chen_seasonal_context": kb.get_hidden_stem_season_context("辰").model_dump(mode="json"),
        "sources": [source.model_dump(mode="json") for source in kb.concepts.sources],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
