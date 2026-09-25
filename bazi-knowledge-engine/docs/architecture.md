# 架構與目前範圍

[回文件導覽](../README.md)

## 一、基礎元素

**Layer 1 — Basic Elements · Status: v1.0 complete**

回答「八字世界裡有哪些東西？每個東西是什麼？」

範圍是陰陽、五行、十天干、十二地支。每個元素的定義包含：

- 基本屬性：穩定 ID、中文名稱，以及適用的順序、陰陽、五行。
- 白話說明：如何理解這個分類、在整體架構中的位置。
- 來源與範圍：傳統象徵的依據，以及哪些部分仍待核對。

例如「甲是陽木」和「甲是十天干之一，在五行與陰陽的分類中屬陽木」同屬元素定義。
木的生長意象可以作為有來源範圍的教學說明，不能因此推論某人的人格。

陰陽 2／2、五行 5／5、十干 10／10、十二支 12／12 都有基本資料、可查詢說明及來源狀態。
十干個別介紹由基本屬性產生；十二支的個別說明存於既有 YAML，透過 `fact_ref`
在查詢時補上基本分類。順序、陰陽與五行只有基本資料一份來源。
十二支可用中文字或 `branch_` 前綴 ID 查詢，既有 `yin` 與 `wu` 查詢意義保留。

v1.0 Freeze 固定這個範圍、schema 與查詢契約。來源版本仍待覆核的地支說明保留
`requires_validation`，天干物象也維持待驗證；完成標記不代表消除已知的考據限制。
個別地支說明沒有動物、時辰、方位、月份、藏干或組合關係。
後續可改善文字與核對來源，但須保留相容性並通過驗收；擴充範圍另行規劃。

## 二、關係／組合規則

回答「元素之間有哪些關係？在明確條件下如何組合？」

| 內容 | 目前狀態 |
| --- | --- |
| 五行相生、相剋 | 已有 YAML 有向關係與直接查詢 |
| 地支到藏干 | 已有十二組有序天干引用，可取得天干基本資料 |
| 地支、藏干與季節 | 已有來源標記及查詢步驟的資料串接 |
| Ten Gods Engine v0.1 | 已實作：日主天干 × 目標天干，十條 YAML 規則與結構化 trace |
| Ten Gods Engine v0.2 | 已實作：明確日主 × 地支，依序取得各藏干的 v0.1 結果及來源 |
| Sexagenary Cycle v0.1 | 已實作：依天干與地支 order 生成 60 個配對，提供合法性與 1-based 序號查詢 |
| Pairwise Interaction Engine v0.1 | 已實作：五合 5、六合 6、六沖 6；明確兩成員查詢 |
| 刑／害／破、三合／三會 | 尚未實作 |
| 通用條件式規則引擎 | 尚未實作 |

固定關係表與可執行推理規則都屬於這一層，但兩者的完成狀態不同。
讀出「寅藏甲、丙、戊」是查表；根據一組前提推導結論，才需要明確的規則與適用條件。
現有季節 API 的 `reference_join` 表示沿引用查找資料，不代表已建立藏干成因公式。

十神是第二層的規則推導：天干 → 五行／陰陽 → 既有五行邊及陰陽同異 → 十神規則。
v0.1 只比較兩個天干；v0.2 先取得指定地支的藏干，再逐一呼叫 v0.1。
兩者均不辨識日柱、不接收命盤，日主由 caller 提供。
結論透過 `rule_id`、結構化五行邊與來源 ID 回溯到基本資料；中文說明只呈現判斷結果。
目前實作採用指定規則，並保留 `requires_validation`，不宣稱已完成歷史考證或科學驗證。

```text
明確日主天干 + 目標地支
                    ↓ get_hidden_stems()
              有序藏干 references → HeavenlyStem
                    ↓ 每個藏干呼叫 get_ten_god(日主, 藏干 ID)
              原 TenGodResult（五行／陰陽 → 規則 → 十神）
                    ↓
              BranchTenGodResult（來源連結 + 有序子結果）
```

v0.2 是第二層既有能力的組合，不新增規則 YAML 或另一套十神引擎。
地支的表面陰陽、五行和季節不參與十神計算；藏干清單只依指定資料展開，不排序或加權。

五行生剋可以在入門時一併介紹，但在架構上屬第二層。
藏干也歸第二層，引用第一層天干；不複製天干的五行或陰陽。

Pairwise v0.1 由 `interactions.py` 獨立承擔規則模型、引用驗證與無方向匹配。
`KnowledgeBase.interactions` 首次查詢才載入兩份規則 YAML 及共用來源 registry；
既有 `_UniqueKeyLoader`、知識目錄定位與讀取函式移至 `_yaml.py` 共用，讀取行為不變。
`get_stem_relations()`／`get_branch_relations()` 是薄的委派入口，不建立通用 Rule Engine。
結果只表示該配對命中哪條規則，不包含合化元素、條件力量、吉凶或柱位置。

## 三、命盤結構

**Layer 3 — Four Pillars Structure v0.1 · Status: implemented**

回答「caller 提供的四柱中有哪些可列出的結構？」Structural analysis only.
四柱以必要的 year／month／day／hour 參數輸入，每柱是兩個中文字：一個天干接一個地支。
先驗證全部引用與六十甲子成員資格，再以日柱天干作為日主。

```text
已知四柱 → 基本引用＋六十甲子驗證 → Pillar × 4 → FourPillars
                       ├─ day.stem → 日主
                       ├─ 年／月／時干 → get_ten_god()
                       └─ 四個地支 → get_branch_ten_gods()
                                     → 原藏干順序與原 TenGodResult
```

日干標示 `role: day_master`，其 visible `ten_god_result` 為 null；
相同天干出現在其他柱時，仍按目標天干處理。
此層只組合 Layer 2 API，不新增生剋、藏干或十神 mapping；月支沒有額外優先或力量判斷。
外層 trace 保存四柱位置與日主選取，嵌套結果保留既有規則 trace 和來源狀態。

單柱六十甲子配對已驗證；年／月及日／時之間的曆法配柱、日期可實現性仍不驗證。
不排盤、不做日期轉四柱，沒有權重、旺衰或解讀；目前不自動掃描 Layer 2 pairwise 關係。
完整輸入契約、模型與範例見 [四柱結構](four-pillars.md)。

## 四、命理解讀

未來才處理旺衰、身強身弱、格局、調候、喜用、大運流年及個人相關解讀。
這些問題需另列流派、前提、來源與適用範圍。目前沒有實作。

期望未來可以從「解讀結果 → 命盤結構 → 關係規則 → 基礎元素」逐層追溯。
來源與可追溯性是各層都要遵守的要求，不另增加一個架構層。

## 架構層與檔案位置

| 責任 | 現有儲存位置 |
| --- | --- |
| 第一層基本屬性 | `knowledge/陰陽`、`五行`、`天干`、`地支` |
| 第一層白話說明與傳統對應 | `knowledge/concepts/` 中相應元素檔案 |
| 第二層五行關係 | `knowledge/五行/five_elements.yaml` 的 `relations` |
| 第二層藏干引用 | `knowledge/hidden_stems.yaml` |
| 第二層十神規則 | `knowledge/ten_gods.yaml`；由既有 `KnowledgeBase` 載入與推導 |
| 第二層季節關聯及關係說明 | `knowledge/concepts/seasons.yaml`、`hidden_stems.yaml` 等 |
| 第二層六十甲子生成與驗證 | `KnowledgeBase.generate_sexagenary_cycle()`；從基本資料 order 推導，不新增 YAML 表 |
| 第二層 Pairwise 關係 | `knowledge/stem_relations.yaml`、`branch_relations.yaml`；`interactions.py` 載入及查詢 |
| 第三層四柱結構 | `models.py` 的四柱模型、`KnowledgeBase.analyze_four_pillars()`；不新增知識 YAML |
| 共用載入、驗證與來源 | `_yaml.py`、既有 `loader.py`／`models.py`、`knowledge/concepts/sources.yaml` |

檔案位置不等於架構層。一個檔案可以包含元素說明和相關關係說明。
`Concept`、`ConceptData`、`fact_ref` 是現有程式／schema 名稱，繼續保留以維持相容性；
它們不是額外的第五層，也不要求把資料複製到新的 `description` 欄位。

第一層 v1.0 保持原樣；第二層已有十神 v0.1 及 v0.2，既有 API 與資料引用方式保持相容。
舊來源 ID 中的 `phase1`、`phase2` 保留作為歷史來源識別，不再作為目前的架構命名。
