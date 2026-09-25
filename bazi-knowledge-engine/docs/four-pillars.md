# Four Pillars Structure v0.1

[回文件導覽](../README.md) · [架構](architecture.md) · [開發參考](development.md) · [來源](sources.md)

**Layer 3 — 命盤結構 · Status: implemented**

**Structural analysis only.** 本版列出已知四柱的日主、明干十神與藏干十神，
讓每個結論可以追溯到第二層規則及第一層基本資料。不進行個人命理解讀。

## 輸入與驗證

```python
from bazi_knowledge import KnowledgeBase

kb = KnowledgeBase()
result = kb.analyze_four_pillars(
    year="丙寅",
    month="辛卯",
    day="壬戌",
    hour="乙巳",
)
```

四個關鍵字都必須提供。每柱恰好兩個中文字：第一個存在於天干資料，第二個存在於地支資料，
且配對必須屬於依基本資料 order 生成的六十甲子。
丙寅、辛卯可以解析；丙、寅、ABC、甲甲、子甲及空字串均失敗。
不自動去除空白，不接受拼音 ID、日期、模型物件或一整行四柱字串。
非字串或參數缺漏為 `TypeError`；非法柱為含位置資訊的 `ValueError`。
四柱全部通過基本解析後才進行 Layer 2 查詢；依賴錯誤會直接傳出。

例如甲丑的兩個字都存在，但配對不屬於六十甲子，會被拒絕。
驗證已包含單柱合法性；不檢查年與月／日與時的曆法一致性，也不證明四柱對應某個實際日期。
生成方法、查詢 API 與完整測試邊界見[六十甲子 v0.1](sexagenary-cycle.md)。
caller 提供已知四柱；生日換算、節氣、時區及排盤都不在 v0.1 範圍。

## 資料模型

解析字串與 canonical 物件分開：API 接收字串，`FourPillars` 保存解析後的 `Pillar`。
模型延伸既有 `models.py`，不另設一套基礎分類或推理 schema。

| 模型 | 欄位與責任 |
| --- | --- |
| `Pillar` | `stem: HeavenlyStem`、`branch: EarthlyBranch`；引用目前載入的基本物件 |
| `FourPillars` | `year`、`month`、`day`、`hour` 四個必要 `Pillar` |
| `VisibleStemAnalysis` | `stem`、`role`、`ten_god_result: TenGodResult \| None` |
| `PillarAnalysis` | `position`、`pillar`、`visible_stem_analysis`、`branch_analysis: BranchTenGodResult` |
| `FourPillarsAnalysis` | `chart`、`day_master`、有序 `pillars`、`trace`、去重 `sources` |

`pillars` 是固定四筆 tuple，順序為 year、month、day、hour；例如 `result.pillars[2]` 是日柱分析。
各柱可經 `result.chart.day` 等名稱取得。結果模型檢查日主、位置順序與子結果所屬柱一致。
物件 frozen 且拒絕額外欄位；可用 `.model_dump()`／`.model_dump_json()` 序列化。

## 日主與明干

`day_master` 直接引用 `chart.day.stem`。caller 不另外指定日主，輸入 day="壬戌" 就選取壬。
年、月、時的天干逐一呼叫 `get_ten_god(day_master.id, stem.id)`，完整保留原結果。

日干是參照點，使用 `role: day_master`、`ten_god_result: null`，優先呈現「日主」。
其餘三干使用 `role: target`。即使另一柱也出現壬，它仍是一般 target，依既有規則得到比肩。
底層 `get_ten_god("壬", "壬")` 的行為不變。

## 四支藏干

每柱均呼叫 `get_branch_ten_gods(day_master.id, branch.id)`。
Layer 3 不重新查一張藏干表，也不重新實作十神邏輯；原 `BranchTenGodResult` 直接嵌入結果。
四個地支的處理一致，月支沒有力量優先。藏干順序與 YAML 相同，不排序、不合併、不加權。

## 指定案例的完整結構摘要

日主：**壬**。

| 位置 | 柱 | 明干角色／十神 | 藏干與十神（原順序） |
| --- | --- | --- | --- |
| year | 丙寅 | 丙 → 偏財 | 甲 → 食神；丙 → 偏財；戊 → 七殺 |
| month | 辛卯 | 辛 → 正印 | 乙 → 傷官 |
| day | 壬戌 | 壬 → 日主 | 戊 → 七殺；辛 → 正印；丁 → 正財 |
| hour | 乙巳 | 乙 → 傷官 | 丙 → 偏財；戊 → 七殺；庚 → 偏印 |

```python
assert result.day_master is result.chart.day.stem
assert result.pillars[2].visible_stem_analysis.role == "day_master"
assert result.pillars[2].visible_stem_analysis.ten_god_result is None

day_hidden = result.pillars[2].branch_analysis.hidden_stem_results
assert [(item.hidden_stem.char, item.ten_god_result.ten_god.name_zh)
        for item in day_hidden] == [("戊", "七殺"), ("辛", "正印"), ("丁", "正財")]
```

完整可執行摘要見 [examples/four_pillars.py](../examples/four_pillars.py)，
加 `--json` 輸出所有基本屬性、結果、trace 和來源記錄。

## Trace 與來源

外層沿用 `TraceStep`，有六個有序 lookup：

1. `chart:input` → `pillars:year`、`pillars:month`、`pillars:day`、`pillars:hour`。
2. 至 5. 各 `pillars:position` → 對應的 `heavenly_stems:id`、`earthly_branches:id`、`sexagenary_cycle:index`。
6. `pillars:day` + 日干基本引用 → `day_master:id`。

這些 chart／pillar／day_master 引用只在本次結果內有效，能由 `chart`、`pillars` 與 `day_master` 欄位解析。
`sexagenary_cycle:index` 的 index 從 1 起；使用同一 KnowledgeBase 生成的循環解析。
每個 Pillar 已包含循環成員的天干／地支 order，序列化結果也保留通過驗證的序號。
外層 `source_ids` 為空 tuple：位置與日主選取是本次使用者規格的 **implementation convention**，
不虛構古籍出處，不宣稱已完成文獻核對。

各 `visible_stem_analysis.ten_god_result.trace` 保留原五步推理。
各 `branch_analysis.trace` 保留地支 → 藏干清單 → 天干引用，再由每個
`hidden_stem_results[*].ten_god_result.trace` 回溯到基本屬性、實際五行邊、陰陽關係及規則 ID。

以日柱戌中的戊為例：

```text
chart:input → pillars:day → earthly_branches:xu
                                 ↓ phase2_spec
                           hidden_stems:xu → heavenly_stems:wu

pillars:day → heavenly_stems:ren → day_master:ren
                                 ↓ 與目標 wu 傳入原十神 API
壬 = 陽水；戊 = 陽土
{source: earth, target: water, relation: controls}
→ target_controls_day_master + same
→ rule_id: qi_sha → 七殺
```

Layer 2 子結果與 trace 保留原物件，不壓成中文一句話。
`sources` 合併所有子結果引用的完整既有來源，藏干與十神各自的 source status 原樣保留。
十神 `requires_validation` 不因四柱串接成功而解除。

## v0.1 的邊界

目前沒有權重、百分比、主中餘氣、月令、旺衰、干支合沖刑害、格局或個人命理解讀。
Hidden stem weighting and qi classification require separate source validation.
現有季節 API 繼續存在，但不參與四柱 v0.1 的計算。
本次停在已知四柱的結構分析；Four Pillars v0.2 尚未實作。
