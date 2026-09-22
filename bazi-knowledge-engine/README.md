# Bazi Knowledge Engine — Phase 1

**這不是算命程式。** 目前的目的是建立機器可讀、可驗證、可追溯的八字基礎知識層。
Basic Data Layer 只描述「這個東西是什麼」，不描述「這個東西代表什麼」。

## 範圍與分層

| 層級 | 責任 | 目前狀態 |
| --- | --- | --- |
| Basic Data | 陰陽、五行、明列的五行相生／相剋、十天干、十二地支基本屬性 | 已實作 |
| Rule | 使用資料與條件進行推導，並記錄適用範圍與來源 | 未實作 |
| Interpretation | 對推導結果提供語意解釋 | 未實作 |

例如 `壬 = yang + water + order 9` 屬於 Basic Data。
五行生剋在本階段是 YAML 中的有向資料關係；查詢只讀取單一方向的直接邊，
不推論反向關係、間接關係或同五行關係。

本階段沒有排盤、出生日期轉四柱、藏干、十神、刑沖合害、旺衰、身強身弱、
喜用神、格局、大運、流年、吉凶、性格或命運分析，也沒有 LLM 解讀、Web UI、
Database、FastAPI、Streamlit、React、Docker 或 LLM API。

## Repository tree

```text
bazi-knowledge-engine/
├── README.md
├── pyproject.toml
├── knowledge/
│   ├── 陰陽/
│   │   └── yin_yang.yaml
│   ├── 五行/
│   │   └── five_elements.yaml
│   ├── 天干/
│   │   └── heavenly_stems.yaml
│   └── 地支/
│       └── earthly_branches.yaml
├── src/
│   └── bazi_knowledge/
│       ├── __init__.py
│       ├── loader.py
│       └── models.py
└── tests/
    ├── test_five_elements.py
    ├── test_heavenly_stems.py
    ├── test_earthly_branches.py
    └── test_loader.py
```

外層 Git repository 保留原有 `.gitattributes`，另有 `.gitignore`。
虛擬環境、快取與建置產物不列入原始碼樹。

## 安裝與測試

需要 Python 3.12+。以下命令從本目錄執行：

```bash
python -m venv .venv
# Windows PowerShell
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q
```

macOS / Linux 將 `.venv/Scripts/python.exe` 換成 `.venv/bin/python`。
執行期只有 PyYAML、Pydantic；pytest 是開發依賴，Hatchling 僅用於封裝。
Wheel 會包含 YAML，因此安裝後可在其他工作目錄查詢。

## 查詢 API

```python
from bazi_knowledge import (
    KnowledgeBase,
    get_heavenly_stem,
    get_earthly_branch,
    get_generating_element,
    get_controlling_element,
    get_element_relation,
)

get_heavenly_stem("壬").model_dump()
# {"id": "ren", "char": "壬", "order": 9, "yin_yang": "yang", "element": "water"}

get_earthly_branch("卯").model_dump()
# {"id": "mao", "char": "卯", "order": 4, "yin_yang": "yin", "element": "wood"}

get_generating_element("水")    # "木"：水所生的五行
get_controlling_element("金")   # "木"：金所剋的五行
get_element_relation("水", "木")  # "generates"
get_element_relation("水", "火")  # "controls"
get_element_relation("木", "水")  # None
get_element_relation("水", "水")  # None

kb = KnowledgeBase()  # 多次查詢時，只需讀取一次 YAML
kb.get_heavenly_stem("甲").element  # "wood"
{item.id: item.name_zh for item in kb.data.yin_yang}  # {"yin": "陰", "yang": "陽"}
```

干支 API 接受單個中文字，回傳不可變的 Pydantic 物件，可用屬性或 `.model_dump()` 讀取。
其 `yin_yang`、`element` 是資料 ID；中文名稱可從 `kb.data.yin_yang`、`kb.data.elements` 查得。
五行 API 接受中文名稱；關係查詢的第一個參數是來源、第二個是目標。
合法五行間沒有直接邊才回傳 Python `None`（JSON 序列化為 `null`）；未知輸入拋出 `KeyError`。

`load_knowledge()` 回傳完整 `KnowledgeData`。
`KnowledgeBase(knowledge_dir=...)` 或 `load_knowledge(knowledge_dir=...)`
可指定另一份相同目錄結構的資料；不會修改原始 YAML。頂層便捷函式每次重新讀取，沒有隱藏快取。

## 資料模型與 YAML schema

所有 YAML 使用 UTF-8。每份檔案頂層是 mapping，集合值是記錄 list。

| YAML 頂層集合 | Pydantic 模型 | 每筆必要欄位 | 筆數 |
| --- | --- | --- | --- |
| `yin_yang` | `YinYang` | `id`, `name_zh` | 2 |
| `elements` | `Element` | `id`, `name_zh`, `order` | 5 |
| `heavenly_stems` | `HeavenlyStem` | `id`, `char`, `order`, `yin_yang`, `element` | 10 |
| `earthly_branches` | `EarthlyBranch` | `id`, `char`, `order`, `yin_yang`, `element` | 12 |
| `relations` | `ElementRelation` | `source`, `target`, `relation` | 10 |

`elements` 與 `relations` 共用 `五行/five_elements.yaml`。例如：

```yaml
# 以下只是完整檔案中的一筆關係示例。
relations:
  - source: water
    target: wood
    relation: generates
```

`id` 是小寫英文字母開頭、其後可接小寫英文字母、數字或底線的穩定識別碼。
ID 在各集合內唯一，不保證跨集合唯一；例如地支 `yin` 是寅，陰陽集合的 `yin` 是陰，
由集合／欄位決定命名空間。`name_zh`、`char` 是單一中文字名稱。
`order` 是從 1 開始、不重複且連續的整數，字串、浮點數及布林值均不接受。
五行依需求採木、火、土、金、水作展示順序，這不是高低排名，也不作為生剋推算依據。

`yin_yang` 必須引用陰陽集合的 ID，`element` 與關係兩端必須引用五行集合的 ID。
`relation` 僅允許 `generates`、`controls`。每種關係的每個五行恰有一條入邊及出邊；
重複／衝突的有向配對、自指、遺漏項目、未知引用與額外欄位都會拒絕載入。
Python 驗證資料形狀與一致性，實際生剋方向只存在 YAML；測試核對需求指定的方向。

Loader 使用 `SafeLoader` 的子類拒絕重複 YAML key，避免後值悄悄覆蓋前值。
四份資料合併後交給 `KnowledgeData` 驗證；物件與集合分別使用 frozen model 與 tuple，
避免查詢結果被意外改寫。缺檔拋出 `FileNotFoundError`，YAML 語法錯誤拋出 `yaml.YAMLError`，
重複 key／頂層格式錯誤拋出 `ValueError`，schema 或引用錯誤拋出 `pydantic.ValidationError`。

## 來源與待核對邊界

YAML 檔首的來源代號對應下表。這是 Phase 1 的檔案層級追溯；目前不建立來源資料庫或推導鏈。
外部資料核對日期：2026-09-22。來源只用於表內指定欄位，其餘內容不匯入。

| 代號 | 來源及適用範圍 |
| --- | --- |
| `phase1-spec` | 本次使用者 Phase 1 規格：陰陽名稱、五行名稱與順序、全部生剋邊、全部天干對應，以及指定的地支驗收值；完整驗收值另存於 tests。 |
| `hko-order` | [香港天文台〈天干和地支〉](https://www.hko.gov.hk/tc/gts/time/stemsandbranches.htm)：十天干與十二地支名稱、順序。 |
| `ndl-elements` | [日本國立國會圖書館〈干支①六十干支〉](https://www.ndl.go.jp/koyomi/chapter3/s1.html)：天干陰陽／五行、十二地支五行表。 |
| `branch-polarity` | [《三命通會》〈論支元六合〉網路轉錄](https://sajumania.com/ebook/to01-05/to01-05-02-21.htm)：僅核對段首列出的陽支與陰支分類，不匯入該章的關係規則。 |

地支 `yin_yang` 表示地支本身的陰陽分類，符合需求指定的子陽水、午陽火等驗收值；
`element` 僅表示地支的本氣五行，不包含任何藏干資料，也不從藏干推導陰陽。

**Requires source validation**：`branch-polarity` 的網路轉錄尚需與指定古籍版本及頁碼覆核；
不同文獻／流派若用「地支陰陽」指其他分類，必須先確認定義、來源與適用範圍，
不得覆寫本層欄位或自行選定爭議規則。
目前未建立任何替代分類。未明確取得來源的未來規則同樣先標記此狀態，不以模型常識補齊。

## 驗收與未來階段

pytest 驗證所有干支的完整對應、陰陽與五行全集、序號唯一且連續、全部十條生剋邊、
所有五行配對的直接查詢語意，以及錯誤資料的拒絕行為。
另以替代 YAML 關係驗證 loader 確實讀取資料，不依 Python 常數或序號計算關係。

未來可以依序規劃以下工作，**本次均未實作**：

1. 先完善來源版本、頁碼與逐筆來源標記。
2. Hidden Stems：核對來源與流派差異後建立獨立 schema。
3. Ten Gods：定義可驗證的規則與測試案例。
4. Stem / Branch Relationships：區分基本關係記錄與條件式規則。
5. Rule Engine：明確列出輸入、適用條件與推導結果。
6. Explainability Layer：回傳引用的資料與規則來源，與 Interpretation 分離。
