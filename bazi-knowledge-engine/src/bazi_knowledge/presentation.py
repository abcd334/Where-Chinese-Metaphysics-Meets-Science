"""Display labels and projections only; no Bazi inference or input validation."""

from .errors import PillarInputError

POSITIONS = {"year": "年", "month": "月", "day": "日", "hour": "時"}
RELATIONS = {"combine": "五合", "six_harmony": "六合", "clash": "六沖"}


def input_error_message(error: PillarInputError) -> str:
    prefix = f"{POSITIONS[error.position]}柱："
    if error.code == "invalid_pair":
        return prefix + f"{error.value}不是目前六十甲子中的合法干支配對。"
    return prefix + "請輸入一個天干 + 一個地支，例如：丙寅。"


def classification_label(stem, facts) -> str:
    polarity = next(item.name_zh for item in facts.yin_yang if item.id == stem.yin_yang)
    element = next(item.name_zh for item in facts.elements if item.id == stem.element)
    return polarity + element


def four_pillars_rows(analysis) -> list[dict[str, str]]:
    rows = [{"項目": name} for name in ("天干", "十神", "地支", "藏干", "藏干十神")]
    for item in analysis.pillars:
        visible = item.visible_stem_analysis
        hidden = item.branch_analysis.hidden_stem_results
        values = (
            item.pillar.stem.char,
            "日主" if visible.role == "day_master" else visible.ten_god_result.ten_god.name_zh,
            item.pillar.branch.char,
            "、".join(entry.hidden_stem.char for entry in hidden),
            "；".join(f"{entry.hidden_stem.char} → {entry.ten_god_result.ten_god.name_zh}" for entry in hidden),
        )
        for row, value in zip(rows, values, strict=True):
            row[POSITIONS[item.position]] = value
    return rows


def interaction_label(interaction) -> str:
    suffix = "干" if interaction.domain == "heavenly_stem" else "支"
    return (f"{POSITIONS[interaction.left_position]}{suffix} {interaction.left_member.char} ↔ "
            f"{POSITIONS[interaction.right_position]}{suffix} {interaction.right_member.char}"
            f"：{RELATIONS[interaction.relation_result.rule.relation]}")


def knowledge_status_rows(analysis, interaction_data) -> list[dict[str, str]]:
    ten_gods = []
    for item in analysis.pillars:
        if item.visible_stem_analysis.ten_god_result is not None:
            ten_gods.append(item.visible_stem_analysis.ten_god_result.ten_god.source_status.value)
        ten_gods.extend(hidden.ten_god_result.ten_god.source_status.value
                        for hidden in item.branch_analysis.hidden_stem_results)
    groups = (
        ("十神", ten_gods),
        ("藏干", [item.branch_analysis.hidden_stem_source_status.value for item in analysis.pillars]),
        ("兩兩關係", [rule.source_status.value for rule in (*interaction_data.stem_relations, *interaction_data.branch_relations)]),
    )
    return [{"知識項目": name, "驗證狀態": "、".join(sorted(set(values)))} for name, values in groups]
