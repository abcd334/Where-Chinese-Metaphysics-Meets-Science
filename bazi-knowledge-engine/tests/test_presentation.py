import pytest

from bazi_knowledge import KnowledgeBase, PillarInputError
from bazi_knowledge.presentation import (
    classification_label, four_pillars_rows, input_error_message, interaction_label, knowledge_status_rows,
)


def test_view_helpers_project_existing_data():
    kb = KnowledgeBase()
    result = kb.analyze_four_pillars(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
    assert classification_label(result.day_master, kb.data) == "陽水"
    rows = four_pillars_rows(result)
    assert rows[0] == {"項目": "天干", "年": "丙", "月": "辛", "日": "壬", "時": "乙"}
    assert rows[1]["日"] == "日主"
    assert rows[4]["日"] == "戊 → 七殺；辛 → 正印；丁 → 正財"
    assert interaction_label(result.stem_interactions[0]) == "年干 丙 ↔ 月干 辛：五合"
    assert interaction_label(result.branch_interactions[0]) == "月支 卯 ↔ 日支 戌：六合"
    statuses = knowledge_status_rows(result, kb.interactions.data)
    assert statuses == [{"知識項目": "十神", "驗證狀態": "requires_validation"},
                        {"知識項目": "藏干", "驗證狀態": "source_attested"},
                        {"知識項目": "兩兩關係", "驗證狀態": "requires_validation"}]


@pytest.mark.parametrize("value,text", [
    ("甲丑", "甲丑不是目前六十甲子中的合法干支配對。"),
    ("ABC", "請輸入一個天干 + 一個地支，例如：丙寅。"),
    ("甲甲", "請輸入一個天干 + 一個地支，例如：丙寅。"),
])
def test_input_error_translation_uses_engine_error(value, text):
    with pytest.raises(PillarInputError) as error:
        KnowledgeBase().analyze_four_pillars(year=value, month="辛卯", day="壬戌", hour="乙巳")
    assert input_error_message(error.value) == "年柱：" + text
