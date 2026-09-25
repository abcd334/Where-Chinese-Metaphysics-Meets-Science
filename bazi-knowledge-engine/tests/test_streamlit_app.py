"""Optional app tests; run with .[app,dev] installed. No browser automation."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_app_can_be_imported_without_running_the_ui():
    spec = importlib.util.spec_from_file_location("bazi_demo_import_test", APP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_default_example_renders_complete_result():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert [item.value for item in app.text_input] == ["丙寅", "辛卯", "壬戌", "乙巳"]
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "壬"
    assert app.dataframe[0].value.iloc[1]["日"] == "日主"
    text = "\n".join(item.value for item in app.markdown)
    assert "年干 丙 ↔ 月干 辛：五合" in text
    assert "月支 卯 ↔ 日支 戌：六合" in text
    assert "水生木" in text and "傷官" in text
    assert any("藏干與十神" in item.label for item in app.expander)
    assert app.session_state["analysis"].day_master.char == "壬"


@pytest.mark.parametrize("value,expected", [("甲丑", "不是目前六十甲子中的合法干支配對"), ("ABC", "請輸入一個天干 + 一個地支")])
def test_invalid_input_is_friendly_and_clears_stale_result(value, expected):
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.button[0].click().run()
    assert app.metric[0].value == "壬"
    app.text_input(key="year").set_value(value)
    app.button[0].click().run()
    assert not app.exception
    assert expected in app.error[0].value
    assert len(app.metric) == 0
    assert "analysis" not in app.session_state


def test_empty_relationship_message_is_scoped_to_current_rules():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    for item in app.text_input:
        item.set_value("甲子")
    app.button[0].click().run()
    assert not app.exception
    assert sum("目前實作的 Pairwise Rule Set 中未偵測到關係。" in item.value for item in app.info) == 2


def test_data_failure_has_no_user_traceback(monkeypatch):
    from bazi_knowledge import KnowledgeBase

    def fail(*args, **kwargs):
        raise FileNotFoundError("internal test path")

    monkeypatch.setattr(KnowledgeBase, "analyze_four_pillars", fail)
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.button[0].click().run()
    assert not app.exception
    assert "知識資料載入或分析失敗" in app.error[0].value
    assert "internal test path" not in app.error[0].value
