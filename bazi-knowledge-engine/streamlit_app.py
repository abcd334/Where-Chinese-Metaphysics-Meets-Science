"""Run: streamlit run streamlit_app.py. UI delegates all rules to bazi_knowledge."""

import logging

import streamlit as st

from bazi_knowledge import KnowledgeBase, PillarInputError
from bazi_knowledge.presentation import (
    POSITIONS, classification_label, four_pillars_rows, input_error_message,
    interaction_label, knowledge_status_rows,
)

LOGGER = logging.getLogger(__name__)
SAMPLE = {"year": "丙寅", "month": "辛卯", "day": "壬戌", "hour": "乙巳"}
EMPTY_RELATIONS = "目前實作的 Pairwise Rule Set 中未偵測到關係。"


@st.cache_resource
def load_kb():
    return KnowledgeBase()


def render_ten_god_trace(result):
    for index, step in enumerate(result.trace, start=1):
        st.write(f"{index}. {step.result}")
    st.caption(f"規則：{result.ten_god.id} · 狀態：{result.ten_god.source_status.value}")


def render_lookup_trace(steps):
    for step in steps:
        st.text(f"{' + '.join(step.input_refs)} → {', '.join(step.output_refs)}")
        if step.source_ids:
            st.caption(f"來源：{', '.join(step.source_ids)}")


def render_analysis(kb, analysis):
    chart_text = " ".join(item.pillar.stem.char + item.pillar.branch.char for item in analysis.pillars)
    st.caption(f"本次分析四柱：{chart_text}")
    st.metric("日主", analysis.day_master.char)
    st.write(classification_label(analysis.day_master, kb.data))

    st.subheader("四柱結構")
    st.dataframe(four_pillars_rows(analysis), hide_index=True, use_container_width=True)

    st.subheader("命盤結構關係 · Detected Relationships")
    for title, interactions in (("天干", analysis.stem_interactions), ("地支", analysis.branch_interactions)):
        st.markdown(f"**{title}**")
        if not interactions:
            st.info(EMPTY_RELATIONS)
        for interaction in interactions:
            st.write(interaction_label(interaction))
            with st.expander(f"查看依據：{interaction_label(interaction)}"):
                render_lookup_trace(interaction.relation_result.trace)
                rule = interaction.relation_result.rule
                st.caption(f"規則：{rule.id} · 狀態：{rule.source_status.value}")
                st.write(rule.source_status.note)

    st.subheader("Why? · 推理過程")
    for item in analysis.pillars:
        visible = item.visible_stem_analysis
        if visible.ten_god_result is not None:
            result = visible.ten_god_result
            with st.expander(f"為什麼{POSITIONS[item.position]}干 {visible.stem.char} 是{result.ten_god.name_zh}？"):
                render_ten_god_trace(result)
        else:
            with st.expander("日主如何取得？"):
                render_lookup_trace((analysis.trace[-1],))
                st.write("日主取自輸入的日柱天干；此處是分析參照點。")
        with st.expander(f"{POSITIONS[item.position]}支 {item.pillar.branch.char}：藏干與十神"):
            render_lookup_trace(item.branch_analysis.trace)
            for hidden in item.branch_analysis.hidden_stem_results:
                st.markdown(f"**{hidden.hidden_stem.char} → {hidden.ten_god_result.ten_god.name_zh}**")
                render_ten_god_trace(hidden.ten_god_result)

    st.subheader("Knowledge Status · 來源與驗證")
    st.dataframe(knowledge_status_rows(analysis, kb.interactions.data), hide_index=True, use_container_width=True)
    st.caption("藏干的 source_attested 指已核對採用的使用者 canonical dataset，不代表全部歷史版本一致。")
    with st.expander("來源記錄與驗證說明"):
        sources = {source.id: source for source in analysis.sources}
        rules = (*kb.interactions.data.stem_relations, *kb.interactions.data.branch_relations)
        rule_source_ids = {source_id for rule in rules for source_id in rule.source_ids}
        sources.update((source.id, source) for source in kb.interactions.data.sources if source.id in rule_source_ids)
        for source in sources.values():
            st.markdown(f"**{source.title}**")
            st.caption(f"{source.id} · 核對日期：{source.checked_on}")
            st.write(source.locator)
            st.write(source.scope)
            if source.url:
                st.markdown(f"[查看來源]({source.url})")
    st.write("本系統將傳統八字規則結構化與程式化，「可驗證」指資料、規則與程式行為可以被追蹤與測試，不代表相關傳統說法已經過現代科學實證。")


def main():
    st.set_page_config(page_title="玄學的盡頭是科學", page_icon="☯", layout="wide")
    st.title("玄學的盡頭是科學")
    st.write("Explainable Bazi Knowledge Engine")
    st.caption("Structured, traceable analysis of traditional Bazi rules.")
    st.info("Structural analysis only. 請輸入已知四柱，本版不提供出生日期排盤。")
    with st.form("four_pillars_form"):
        inputs = {}
        for column, (position, default) in zip(st.columns(4), SAMPLE.items(), strict=True):
            with column:
                inputs[position] = st.text_input(f"{POSITIONS[position]}柱 · {position.title()} Pillar", default, key=position)
        submitted = st.form_submit_button("分析 · Analyze", type="primary")

    if submitted:
        st.session_state.pop("analysis", None)
        try:
            st.session_state["analysis"] = load_kb().analyze_four_pillars(**inputs)
        except PillarInputError as error:
            st.error(input_error_message(error))
        except Exception:
            LOGGER.exception("Knowledge engine could not complete analysis")
            st.error("知識資料載入或分析失敗，請確認安裝與資料檔案完整後重試。")

    if "analysis" in st.session_state:
        render_analysis(load_kb(), st.session_state["analysis"])
    else:
        st.caption("可直接按 Analyze 查看預設範例：丙寅 辛卯 壬戌 乙巳。")
    st.divider()
    st.caption("目前不提供吉凶、性格、財運、工作、婚姻、健康、旺衰、喜用神、格局、大運或流年解讀。")


if __name__ == "__main__":
    main()
