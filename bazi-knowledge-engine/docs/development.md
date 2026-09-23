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
    │   ├── relationships.md
    │   ├── development.md
    │   └── sources.md
    ├── examples/
    │   └── inspect_knowledge.py
    ├── knowledge/
    │   ├── 陰陽/yin_yang.yaml
    │   ├── 五行/five_elements.yaml
    │   ├── 天干/heavenly_stems.yaml
    │   ├── 地支/earthly_branches.yaml
    │   ├── hidden_stems.yaml
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
    │   └── models.py
    └── tests/
        ├── test_five_elements.py
        ├── test_heavenly_stems.py
        ├── test_earthly_branches.py
        ├── test_hidden_stems.py
        ├── test_concepts.py
        ├── test_layer1.py
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

`ConceptData` 合併七份說明資料，含 28 筆儲存的說明、11 筆來源、4 季及 12 筆地支季節位置。
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

同一 YAML reader 使用 SafeLoader 子類並拒絕重複 key。

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
