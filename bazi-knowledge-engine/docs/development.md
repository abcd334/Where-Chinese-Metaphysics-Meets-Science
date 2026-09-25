# 開發參考

[回文件導覽](../README.md) · [架構](architecture.md) · [來源](sources.md)

## 目錄與執行

```text
Where Chinese Metaphysics Meets Science/
├── README.md                         # GitHub 入口
├── .gitattributes
├── .gitignore
└── bazi-knowledge-engine/
    ├── README.md                     # 專案導覽與快速開始
    ├── TODO.md                       # 待辦與待驗證事項
    ├── pyproject.toml
    ├── docs/
    │   ├── architecture.md
    │   ├── basic-elements.md
    │   ├── four-pillars.md
    │   ├── sexagenary-cycle.md
    │   ├── relationships.md
    │   ├── development.md
    │   └── sources.md
    ├── examples/
    │   ├── inspect_knowledge.py
    │   ├── ten_gods.py
    │   ├── branch_ten_gods.py
    │   ├── four_pillars.py
    │   ├── sexagenary_cycle.py
    │   └── interactions.py
    ├── knowledge/
    │   ├── 陰陽/yin_yang.yaml
    │   ├── 五行/five_elements.yaml
    │   ├── 天干/heavenly_stems.yaml
    │   ├── 地支/earthly_branches.yaml
    │   ├── hidden_stems.yaml
    │   ├── ten_gods.yaml
    │   ├── stem_relations.yaml
    │   ├── branch_relations.yaml
    │   └── concepts/
    │       ├── sources.yaml
    │       ├── seasons.yaml
    │       ├── yin_yang.yaml
    │       ├── five_elements.yaml
    │       ├── heavenly_stems.yaml
    │       ├── earthly_branches.yaml
    │       └── hidden_stems.yaml
    ├── src/bazi_knowledge/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── _yaml.py
    │   ├── interactions.py
    │   └── models.py
    └── tests/
        ├── test_five_elements.py
        ├── test_heavenly_stems.py
        ├── test_earthly_branches.py
        ├── test_hidden_stems.py
        ├── test_concepts.py
        ├── test_layer1.py
        ├── test_ten_gods.py
        ├── test_branch_ten_gods.py
        ├── test_four_pillars.py
        ├── test_sexagenary_cycle.py
        ├── test_interactions.py
        ├── test_seasonal_context.py
        └── test_loader.py
```

省略 Git 內部檔案、虛擬環境、快取與建置產物。檔案位置沿用既有架構，
`concepts/` 是說明及相關資料的儲存目錄，不是獨立架構層。

需要 Python 3.12+；在 `bazi-knowledge-engine/` 目錄執行：

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -X utf8 examples/inspect_knowledge.py
.venv/Scripts/python.exe -X utf8 examples/ten_gods.py
```

macOS／Linux 將 Python 路徑換成 `.venv/bin/python`。
執行期為 PyYAML、Pydantic；pytest 是開發依賴，Hatchling 用於封裝。
Wheel 包含 knowledge YAML，安裝後不依賴來源 checkout 的工作目錄；sdist 包含文件與範例。

## 查詢 API

以下查詢同時提供頂層函式與 `KnowledgeBase` 方法。
多次查詢建議共用一個 `KnowledgeBase`，避免重複載入；頂層便捷函式每次建立新實例。

| API | 輸入 | 回傳 |
| --- | --- | --- |
| `get_heavenly_stem` | 天干中文字 | `HeavenlyStem` |
| `get_earthly_branch` | 地支中文字 | `EarthlyBranch` |
| `get_generating_element` | 五行中文名 | 該五行所生的五行中文名 |
| `get_controlling_element` | 五行中文名 | 該五行所剋的五行中文名 |
| `get_element_relation` | 來源、目標五行中文名 | `generates`、`controls` 或 `None` |
| `get_hidden_stems` | 地支中文字或 ID | 有序 `list[HeavenlyStem]` |
| `get_concept` | 說明 ID／中文名、天干 ID／中文字、地支中文字或 `branch_` 說明 ID | `Concept` |
| `get_hidden_stem_season_context` | 地支中文字或 ID | `HiddenStemSeasonContext` |
| `get_ten_god` | 日主天干、目標天干：各接受中文字或天干 ID | `TenGodResult` |
| `get_branch_ten_gods` | 日主天干、地支：各接受中文字或所屬集合 ID | `BranchTenGodResult` |
| `analyze_four_pillars` | 必要關鍵字 year／month／day／hour，各為中文干支字串 | `FourPillarsAnalysis` |
| `generate_sexagenary_cycle` | 無參數 | 有序 `tuple[Pillar, ...]`，60 筆 |
| `is_valid_pillar` | 中文干支字串 | `bool`；非字串拋出 `TypeError` |
| `get_sexagenary_index` | 合法中文干支字串 | 1–60 的整數；非法字串拋出 `ValueError` |
| `get_stem_relations` | 兩個天干中文字或 ID | `tuple[StemRelationResult, ...]` |
| `get_branch_relations` | 兩個地支中文字或 ID | `tuple[BranchRelationResult, ...]` |
| `classify_element_relation` | 日主五行、目標五行：各接受中文名或 ID | 五種日主視角的關係分類之一 |

```python
from bazi_knowledge import KnowledgeBase

kb = KnowledgeBase()
assert kb.get_heavenly_stem("壬").model_dump() == {
    "id": "ren", "char": "壬", "order": 9, "yin_yang": "yang", "element": "water",
}
assert kb.get_earthly_branch("卯").element == "wood"
assert kb.get_generating_element("水") == "木"
assert kb.get_controlling_element("金") == "木"
assert kb.get_element_relation("水", "木") == "generates"
assert kb.get_element_relation("水", "火") == "controls"
assert kb.get_element_relation("木", "水") is None
assert kb.get_element_relation("水", "水") is None

assert [stem.char for stem in kb.get_hidden_stems("yin")] == ["甲", "丙", "戊"]
assert kb.get_hidden_stems("xu")[1] is kb.get_heavenly_stem("辛")
assert kb.get_concept("wood") == kb.get_concept("木")
assert kb.get_concept("甲").source_status.value == "derived_from_facts"
```

基本屬性的 `yin_yang`、`element` 是 ID；中文名從 `kb.data.yin_yang`、`kb.data.elements` 取得。
物件可用屬性或 `.model_dump()` 讀取。未知輸入拋出 `KeyError`；只有合法五行間沒有直接邊時才回傳 `None`。
藏干回傳新 list，其中元素直接引用已載入的不可變天干物件；修改 list 不會更改儲存的有序引用。

說明查詢支援陰陽、五行、干支整體、相生／相剋、藏干與季節相關概念及二十二個干支的個別介紹。
`get_concept("卯")` 與 `get_concept("branch_mao")` 都能查詢；基本屬性仍使用 `get_earthly_branch("卯")`。
`get_concept("yin")` 是陰；`get_hidden_stems("yin")` 是寅的藏干。
`get_concept("wu")` 仍是戊；地支說明一律用中文字或 `branch_` 前綴 ID，沒有新增裸地支 ID 別名。
藏干 API 的 `wu` 指午，藏干清單裡的天干 ID `wu` 才指戊。

季節 API 範例與推導界線見[關係資料](relationships.md)。回傳的 `trace` 是查詢紀錄：
`operation` 為 lookup／join，`input_refs`、`output_refs` 使用 `collection:id`，另有 `source_ids`。
已載入的天干與元素說明及待驗證狀態均保留，不把查詢串接升格為成因驗證。

## 基本資料與關係 schema

所有 YAML 使用 UTF-8；頂層是 mapping，下列集合值是記錄 list。
模型共用 `models.py` 中的 frozen `DataModel`，拒絕額外欄位；載入後集合使用 tuple。

| 集合 | 模型 | 每筆欄位 | 筆數 |
| --- | --- | --- | --- |
| `yin_yang` | `YinYang` | `id`, `name_zh` | 2 |
| `elements` | `Element` | `id`, `name_zh`, `order` | 5 |
| `heavenly_stems` | `HeavenlyStem` | `id`, `char`, `order`, `yin_yang`, `element` | 10 |
| `earthly_branches` | `EarthlyBranch` | `id`, `char`, `order`, `yin_yang`, `element` | 12 |
| `relations` | `ElementRelation` | `source`, `target`, `relation` | 10 |
| `hidden_stems` | `HiddenStemSet` | `branch_id`, `stem_ids` | 12 |

`elements`、`relations` 共用五行檔案。下列是部分記錄示例，不是可獨立載入的完整資料集：

```yaml
relations:
  - source: water
    target: wood
    relation: generates
```

```yaml
hidden_stems:
  - branch_id: zi
    stem_ids: [gui]
  - branch_id: chou
    stem_ids: [ji, gui, xin]
  - branch_id: yin
    stem_ids: [jia, bing, wu]
```

`id` 為小寫字母開頭，後續可接小寫字母、數字或底線，在集合內唯一。
基本資料的 `name_zh`、`char` 為單一中文字；`order` 為從 1 起連續且唯一的整數，不接受字串、浮點或布林值。
干支陰陽與五行必須引用既有集合。

`relation` 限 `generates`／`controls`，每種關係的每個五行恰有一條入邊和出邊；
不接受自指、重複、衝突、遺漏或未知引用。方向存在 YAML 中，Python 不硬編碼生剋表。

十二地支各有且只有一筆藏干 mapping；`stem_ids` 必須非空、無重複且全部引用存在的天干。
Loader 保留清單順序，pytest 核對採用的完整對應與順序。不接受重複天干屬性、權重或氣分類欄位。

## 說明、季節與來源 schema

`Concept` 是現有模型名稱，承載元素或關係的白話說明；不代表獨立架構層。

| 模型 | 欄位 |
| --- | --- |
| `Concept` | `id`, `name_zh`, `fact_ref`（可省略）, `short_definition`, `plain_explanation`, `traditional_associations`, `notes`, `source_ids`, `source_status` |
| `TraditionalAssociation` | `kind`（symbol／season／direction）, `value`, `scope`, `source_ids`, `source_status` |
| `Source` | `id`, `title`, `url`（可為 null）, `locator`, `scope`, `checked_on` |
| `SourceStatus` | `value`, `note`；狀態語意見[來源文件](sources.md) |
| `Season` | `id`, `name_zh` |
| `BranchSeason` | `branch_id`, `season_id`, `stage`（孟／仲／季）, `scope`, `source_ids`, `source_status` |

元素說明的 `fact_ref` 以 `{collection: elements, id: wood}` 等形式引用基本資料。
定義與解釋使用非空繁體中文字串；說明名稱不限單一字。
各 association 分別保存適用範圍與來源狀態。十干個別介紹直接從目前基本屬性產生，
不在說明 YAML 再存一份陰陽五行 mapping。

十二支個別記錄沿用相同 `Concept` schema，`id` 為 `branch_zi` 等，
`fact_ref` 指向 `earthly_branches`。YAML 的定義與解釋只存不含分類值的文字；
`get_concept()` 補上所引用基本資料的順序、陰陽與五行，不修改儲存的 Concept。
因此 `load_concepts()` 提供原始說明，`get_concept()` 提供含基本分類的完整說明。
查詢保留原 `source_ids` 與 `source_status`，不以 `derived_from_facts` 蓋掉地支的待驗證狀態。

`ConceptData` 合併七份說明資料，含 28 筆儲存的說明、13 筆共用來源、4 季及 12 筆地支季節位置。
十干動態介紹不算在這 28 筆中。驗證包含 ID／名稱唯一、來源引用、基本資料引用與季節位置完整性，
並要求十二支說明全部有引用，且中文名與引用的地支一致。
Schema 能檢查形狀和引用，不能自動判斷所有自然語言內容是否越界，文字仍需人工審閱。

## 載入與錯誤

`load_knowledge(knowledge_dir=...)` 回傳 `KnowledgeData`，一次讀取四份基本分類檔案及藏干檔案。
`KnowledgeBase(knowledge_dir=...)` 可使用自訂同結構目錄。
自訂資料必須包含 `hidden_stems.yaml`；缺檔時不會混入預設資料。

`load_concepts(knowledge_dir=..., facts=...)` 回傳 `ConceptData` 並對基本資料驗證引用。
`KnowledgeBase.concepts` 首次使用才載入並保存在該實例中；不查詢說明時不需要 `concepts/` 目錄。
說明查詢缺檔會明確報錯，不回退到其他資料目錄。

同一 YAML reader 使用 SafeLoader 子類並拒絕重複 key，現位於 `_yaml.py`，由既有與新領域共用。

| 問題 | 錯誤 |
| --- | --- |
| 缺少必要檔案 | `FileNotFoundError` |
| YAML 語法錯誤 | `yaml.YAMLError` |
| 重複 key／頂層格式不符 | `ValueError` |
| Schema 或引用不符 | `pydantic.ValidationError` |
| 說明載入後對基本資料的跨集合核對不符 | `ValueError` |
| 查詢不存在的值 | `KeyError` |

## 測試與修改原則

既有 pytest 涵蓋完整分類、順序、生剋方向、藏干引用與順序、非法資料拒絕、來源引用、
動態天干說明、季節查詢 trace 與未驗證狀態保留。
測試會修改暫存 YAML，確認查詢跟隨資料，而不是依 Python 常數推算。

修改資料時同時核對來源、引用與文件示例；新規則先寫清楚前提和範圍。
Layer 1 — Basic Elements 的 **Status: v1.0 complete** 是知識範圍及查詢契約的完成標記，
不是整個 Python 套件的發行版本；`pyproject.toml` 版本不因此改成 1.0。
`test_layer1.py` 驗收 29 個基本元素的說明、引用、來源、欄位與文字邊界；
文字檢查是目前資料集的回歸保護，不是通用自然語言判讀器。
待考據項目及後續建議見 [TODO](../TODO.md)。

## Ten Gods Engine v0.1

十神使用既有 `KnowledgeBase`、`DataModel`、`Source`、`SourceStatus` 和嚴格 YAML reader。
原基本資料、藏干、季節及 Concept API 不變。新 API 不接受模型物件，只接受天干名稱或 ID 字串；
例如 `wu` 在此指天干戊，`午`、`yin`、出生日期字串均拋出 `KeyError`。
非字串（包括地支物件、list、dict）拋出 `TypeError`。

```python
from bazi_knowledge import KnowledgeBase, get_ten_god, classify_element_relation

kb = KnowledgeBase()
result = kb.get_ten_god("壬", "乙")
assert result == get_ten_god("ren", "yi")
assert result.day_master is kb.get_heavenly_stem("壬")
assert result.target is kb.get_heavenly_stem("乙")
assert result.ten_god.name_zh == "傷官"
assert result.trace[-1].rule_id == "shang_guan"
assert result.ten_god.source_status.value == "requires_validation"
assert classify_element_relation("water", "metal") == "target_generates_day_master"
payload = result.model_dump(mode="json", exclude_none=True)
```

### 規則 schema

`knowledge/ten_gods.yaml` 頂層為 `stem_source_ids`、`element_source_ids`、`ten_gods`。
前兩者列出 trace 引用的既有天干／五行關係來源；`ten_gods` 是十筆規則。
下例是部分記錄，不是可單獨載入的完整規則表：

```yaml
stem_source_ids: [phase1_spec, hko_order, ndl_elements]
element_source_ids: [phase1_spec]
ten_gods:
  - id: shang_guan
    name_zh: 傷官
    aliases: []
    element_relation: day_master_generates_target
    polarity_relation: different
    source_ids: [ten_gods_v01_spec]
    source_status:
      value: requires_validation
      note: 使用者 canonical implementation specification，尚待歷史文獻版本核對。
```

`TenGod` 同時保存名稱與匹配條件；名稱與規則一對一，因此 `id` 也是 `rule_id`，
不用另一張十神結果表。五行分類值見[完整關係表](relationships.md)，陰陽分類只允許 `same`／`different`。
`aliases` 預設為空；七殺記錄偏官別名。程式不以 alias 判斷規則。

`TenGodData` 保存十條規則、來源記錄及兩種基本來源 ID 清單，驗證：

- 十條記錄、唯一 ID 與中文名，alias 不可重複或與 canonical name 衝突。
- 五種五行分類 × 兩種陰陽分類，每組恰有一條規則，拒絕缺漏或重複。
- 來源 ID 必須存在於共用 registry，來源 ID 不可重複定義；來源清單不可為空。
- 所有模型拒絕額外欄位，名稱與來源說明不得為空。

`load_ten_gods(knowledge_dir=...)` 讀取規則及既有 `concepts/sources.yaml`，不載入其他說明或季節檔案。
`KnowledgeBase.ten_gods` 首次使用才載入並快取。缺少十神檔案時，舊 API 照常工作；
十神查詢拋出 `FileNotFoundError`，不回退到預設規則。
自訂目錄需提供同一結構的來源 registry；新來源 ID 也必須在該目錄中登錄。

### 結果與 trace

| 模型 | 欄位 |
| --- | --- |
| `TenGodResult` | `ten_god`, `day_master`, `target`, `element_relation`, `polarity_relation`, `trace`, `sources` |
| `ReasoningStep` | `step`, `input_refs`, `output_refs`, `result`, `source_ids`；適用步驟另有 `element_relation`, `element_edge`, `polarity_relation`, `rule_id` |

`trace` 為五步有序 tuple：resolve_day_master、resolve_target、element_relation、polarity_relation、ten_god_rule。
`input_refs`／`output_refs` 沿用 `collection:id` 格式；`element_relation:...` 和 `polarity_relation:...`
是本次運算的中間結果，其他引用對應已載入的基本資料或規則。
五行步驟保留實際使用的有向 `ElementRelation`；同五行時 `element_edge` 為 null。
中文 `result` 只是結構化判斷的呈現，不是規則輸入。

結果中的天干與十神物件引用已載入資料，`sources` 提供這五步所使用來源的完整記錄。
規則 `source_status` 原樣保留，不因匹配成功變成已驗證。物件 frozen、集合 tuple，並可 JSON 序列化。

新分類器對不同五行檢查既有生剋邊的正反方向；若候選不是恰好一條，拋出 `ValueError`。
此限制只作用於十神分類，沒有改動第一層或原直接邊查詢的行為。

`test_ten_gods.py` 覆蓋壬／甲日主指定案例、100 組配對、每個日主十神各一次、完整 trace、
不合法輸入／規則／來源，以及修改暫存 YAML 後結論隨資料變動的測試。
此 API 仍只處理兩個天干；地支藏干展開由下列 v0.2 API 組合處理。

## Ten Gods Engine v0.2

```python
from bazi_knowledge import KnowledgeBase, BranchTenGodResult, get_branch_ten_gods

kb = KnowledgeBase()
result = kb.get_branch_ten_gods("壬", "戌")
assert result == get_branch_ten_gods("ren", "xu")
assert result.branch is kb.get_earthly_branch("戌")
assert result.hidden_stem_results[0].hidden_stem is kb.get_heavenly_stem("戊")
assert result.hidden_stem_results[0].ten_god_result.ten_god.name_zh == "七殺"
assert BranchTenGodResult.model_validate_json(result.model_dump_json()) == result
```

`get_branch_ten_gods(day_master, branch)` 兩個必要參數只接受字串。
日主使用 v0.1 天干查詢；地支使用藏干查詢既有的中文字或 ID 規則。
例如 `("wu", "wu")` 指戊日主與午地支；`("ren", "yin")` 指壬日主與寅地支。
`branch_xu` 是 Concept ID，不是這個 API 的地支 ID。
未知或不合範圍的字串拋出 `KeyError`，非字串（含模型物件）拋出 `TypeError`。
caller 必須提供日主；不接受四柱或日期，不做自動辨識。

| 模型 | 欄位 |
| --- | --- |
| `BranchTenGodResult` | `day_master`, `branch`, `hidden_stem_results`, `trace`, `hidden_stem_source_status`, `sources` |
| `HiddenStemTenGodResult` | `hidden_stem: HeavenlyStem`, `ten_god_result: TenGodResult` |

`hidden_stem_results` 為非空 tuple，順序與 `get_hidden_stems()` 完全相同。
每個 `ten_god_result` 直接保留 `get_ten_god()` 回傳物件，包含原五步 trace、規則及來源。
外層沿用 `TraceStep` 保存兩步：`earthly_branches:id → hidden_stems:id` 的 lookup，
以及 `hidden_stems:id → heavenly_stems:id...` 的 join。輸出引用依藏干順序排列。
結構化引用是追溯依據；不另外建立一份自然語言判斷邏輯。

藏干 lookup／join 的 `source_ids` 與 `hidden_stem_source_status` 取自既有
`get_concept("hidden_stems")`。`sources` 包含藏干與所有子結果所用來源的完整去重記錄。
因此本 API 除基本資料與十神規則外，也會透過既有 Concept loader 載入完整 `concepts/`，
沿用其來源及跨集合驗證；季節資料不參與十神判斷。
自訂目錄需要同樣結構，缺檔或驗證失敗直接報錯，不回退至預設資料或回傳部分結果。
原 v0.1 仍只需要基本資料、十神規則及來源 registry，沒有新增其載入依賴。

全部模型沿用 frozen、禁止額外欄位及 JSON 序列化設定；不新增權重、百分比、氣分類或解讀欄位。
v0.2 沒有新增 YAML schema 或依賴，藏干與十神規則只有既有資料一份來源。

```powershell
.venv/Scripts/python.exe -X utf8 examples/branch_ten_gods.py
.venv/Scripts/python.exe -m pytest -q
```

`test_branch_ten_gods.py` 覆蓋全部 120 個配對及 280 個子結果與 v0.1 一致、
中文／ID 相容性、順序、物件重用、trace 引用、來源狀態、JSON 往返及錯誤邊界。
測試會改動暫存藏干清單及 provenance，確認結果跟隨 YAML，並驗證地支表面分類不影響十神。

## Four Pillars Structure v0.1

**Layer 3 · Status: implemented — Structural analysis only.**
完整模型與使用契約見 [four-pillars.md](four-pillars.md)，本節列出開發入口。

```python
from bazi_knowledge import KnowledgeBase, FourPillarsAnalysis

kb = KnowledgeBase()
result = kb.analyze_four_pillars(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
assert result.day_master is result.chart.day.stem
assert result.pillars[2].visible_stem_analysis.role == "day_master"
assert result.pillars[2].visible_stem_analysis.ten_god_result is None
assert FourPillarsAnalysis.model_validate_json(result.model_dump_json()) == result
```

亦匯出同名 module-level wrapper。輸入限四個明確關鍵字與中文字串，
不接受 `FourPillars` 物件或 stable ID；`FourPillars` 保存解析後的 canonical 物件。
缺少／額外參數或非字串拋出 `TypeError`；長度、順序或字元集合不符拋出含柱位置的 `ValueError`。
API 先透過原 `get_heavenly_stem()`、`get_earthly_branch()` 驗證全部四柱，
並呼叫 `get_sexagenary_index()` 驗證每柱配對，全部通過後再呼叫三次明干 `get_ten_god()` 和四次 `get_branch_ten_gods()`。
後者仍在 Layer 2 中逐一呼叫藏干十神，原結果物件不重建也不壓縮 trace。

沿用 v0.2 的知識目錄與延遲載入要求，無新 dependency 或 YAML schema。
來源或 Layer 2 驗證失敗會直接傳出，不回傳部分分析。
新模型沿用 frozen／禁止額外欄位／tuple；額外檢查日主、柱位置順序及子結果所屬柱一致。

```powershell
.venv/Scripts/python.exe -X utf8 examples/four_pillars.py
.venv/Scripts/python.exe -X utf8 examples/four_pillars.py --json
.venv/Scripts/python.exe -m pytest -q
```

`test_four_pillars.py` 覆蓋 canonical 案例全部明干與藏干、所有位置的非法輸入、
十個日干切換、重複柱、API 結果重用、trace／來源、JSON 往返與結構一致性。
現已加上六十甲子成員驗證，十個日主測試各選循環中合法的日柱；不加入月令或日期規則。

## Sexagenary Cycle v0.1

沿用 `Pillar` 與原基本物件；按兩個集合的 `order` 排序，利用 Python 標準庫 `math.lcm`
決定循環長度。查詢成員與序號均使用同一個生成方法，不建立額外的陰陽捷徑或 60 筆表。
三個 API 也有 module-level wrapper。完整契約見 [sexagenary-cycle.md](sexagenary-cycle.md)。

`test_sexagenary_cycle.py` 驗證完整性、唯一性、首尾及跨界序號、每干 6 次／每支 5 次、
120 種配對分類、60 柱通過四柱 API、每個位置的非法配對在 Layer 2 分析前被拒絕，
以及改動暫存 YAML order 後生成結果隨之改變。

```powershell
.venv/Scripts/python.exe -X utf8 examples/sexagenary_cycle.py
.venv/Scripts/python.exe -m pytest -q
```

## Pairwise Interaction Engine v0.1

`interactions.py` 是具體的兩成員關係領域，包含模型、規則載入、驗證與查詢。
沿用 `DataModel`、`Identifier`、`Source`、`SourceStatus`、`TraceStep` 及基本干支物件。
共用 YAML reader 僅從 `loader.py` 原樣抽出；舊載入函式與查詢契約不變。
沒有新 dependency、第二套五行表、通用條件引擎或四柱掃描。

### 規則與結果 schema

| 模型 | 欄位 |
| --- | --- |
| `StemRelation` | `id`, `relation: combine`, `members`（恰好兩個天干 ID）, `source_ids`, `source_status` |
| `BranchRelation` | `id`, `relation: six_harmony \| clash`, `members`（恰好兩個地支 ID）, `source_ids`, `source_status` |
| `InteractionData` | `stem_relations`, `branch_relations`, `sources` |
| `StemRelationResult` | `rule: StemRelation`, `members: tuple[HeavenlyStem, HeavenlyStem]`, `trace`, `sources` |
| `BranchRelationResult` | `rule: BranchRelation`, `members: tuple[EarthlyBranch, EarthlyBranch]`, `trace`, `sources` |

兩份 YAML 分別只提供 `stem_relations` 與 `branch_relations`，來源仍存於共用 registry。
`PairwiseRule` 僅共用規則欄位，Python 不存配對常數。匹配以成員 ID 的無序集合比較，
結果依 YAML 規則順序排列；members 物件依 caller 輸入順序排列。
未命中（包含同一成員重複查詢）回傳空 tuple；不把未命中當成吉凶或其他關係。

載入時驗證：

- 五合恰 5 條，六合／六沖各 6 條；全域 rule ID 唯一。
- 每條恰兩個不同成員，引用必須存在於所屬天干或地支集合。
- 同類型無方向配對唯一；同類型內每個干或支恰出現一次，避免漏掉成員。
- 來源 ID 清單非空且不重複，所有 ID 均能在唯一的來源 registry 中解析。
- source status 使用既有列舉與說明；拒絕額外欄位，例如 transformation／weight／fortune。

配對是否與採用清單一致由 canonical 測試驗收；schema 不硬編碼 17 個配對。

```python
from bazi_knowledge import KnowledgeBase, StemRelationResult, get_stem_relations

kb = KnowledgeBase()
result, = kb.get_stem_relations("bing", "xin")
assert result == get_stem_relations("丙", "辛")[0]
assert result.members[0] is kb.get_heavenly_stem("丙")
assert result.rule.source_status.value == "requires_validation"
assert StemRelationResult.model_validate_json(result.model_dump_json()) == result
```

`KnowledgeBase.interactions` 是延遲載入的 `InteractionEngine`，其 `.data` 提供已驗證的完整規則。
首次 pairwise 查詢會讀取兩份規則檔與 `concepts/sources.yaml`，不讀其他 Concept／季節／十神檔案。
缺檔或壞資料直接報錯，不回退預設資料。相對自訂目錄沿用 KnowledgeBase 的絕對路徑定位。
未使用 pairwise API 時不需要這兩份新規則檔；Four Pillars v0.1 也不觸發它們。
兩個 API 均有 module-level wrapper；參數非字串為 TypeError，未知或跨集合字串為 KeyError。

結果 frozen、tuple 且可 JSON 往返；`trace` 為一個 lookup，基本成員引用指向規則引用，
`source_ids` 取自原規則，`sources` 回傳該規則使用的完整來源記錄。
沒有重新計算藏干／十神，也沒有替關係加入自然語言推論。

```powershell
.venv/Scripts/python.exe -X utf8 examples/interactions.py
.venv/Scripts/python.exe -m pytest -q
```

`test_interactions.py` 窮舉 100 個天干、144 個地支有序輸入，包含 17 條規則的正反方向、
無關及同成員查詢。另驗證來源與物件引用、JSON、壞 YAML／規則拒絕、自訂資料改動生效、
延遲載入，以及原四柱功能不自動查詢 pairwise 關係。
