# 八字 Knowledge Engine

這是一個機器可讀、可驗證、可追溯的八字知識庫，目前還不是算命程式。
**Layer 1 — Basic Elements**

**Status: v1.0 complete**

陰陽 2／2、五行 5／5、十天干 10／10、十二地支 12／12 均具備
Basic Fact ＋ Plain Explanation ＋ Source / Validation Status。
v1.0 凍結目前的基本分類、引用方式與查詢契約；待考據的來源狀態仍如實保留，
不表示所有傳統說法已完成文獻驗證。後續變更須同步更新測試與文件。

## 四層架構

```text
1. 基礎元素 — v1.0 complete
   陰陽、五行、天干、地支：基本屬性＋白話說明
        ↓ 被引用
2. 關係／組合規則
   生剋、藏干、季節關聯、Ten Gods v0.2；合沖刑害尚未實作
        ↓ 未來組合
3. 命盤結構
   整張四柱的結構分析（尚未實作）
        ↓ 未來解讀
4. 命理解讀
   旺衰、格局、喜用、大運流年等（尚未實作）
```

「含義」是元素定義的一部分，不另設 Concept 架構層。
例如甲的基本屬性是「天干第 1 位、陽、木」，白話說明是「甲是十天干之一，在五行與陰陽的分類中屬陽木」。
這些內容不推論人的性格或命運。

第二層已有五行生剋、十二地支藏干、藏干與季節的關聯查詢，以及 **Ten Gods Engine v0.2**。
十神以兩個天干的五行方向與陰陽同異匹配十條 YAML 規則，包含結構化推理紀錄。
v0.2 串接既有藏干查詢與 v0.1，依原藏干順序回傳每個天干的十神及完整 trace。
目前尚未實作通用 Rule Engine 或命盤組合分析。
四層是責任分工，不代表四層都已完成，也不要求依層號刪除已存在的功能。

## 文件導覽

| 想了解的事情 | 文件 |
| --- | --- |
| 陰陽、五行、每個天干和地支是什麼？ | [基礎元素入門](docs/basic-elements.md) |
| 四層如何分工？哪些已完成？ | [架構與目前範圍](docs/architecture.md) |
| 生剋、藏干、四季與十神如何查詢？ | [關係資料](docs/relationships.md) |
| 如何安裝、查詢、修改 YAML 與執行測試？ | [開發參考](docs/development.md) |
| 資料從哪裡來？哪些說法還不能確定？ | [來源與驗證邊界](docs/sources.md) |
| 接下來先整理什麼？ | [待辦清單](TODO.md) |

初次閱讀建議從「基礎元素入門」開始；不需要先理解 Python 模型或 YAML schema。

## 快速開始

需要 Python 3.12+。在 `bazi-knowledge-engine/` 目錄執行：

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest -q
```

macOS／Linux 使用 `.venv/bin/python`。執行期依賴只有 PyYAML、Pydantic。

```python
from bazi_knowledge import KnowledgeBase

kb = KnowledgeBase()
assert kb.get_heavenly_stem("甲").element == "wood"
assert kb.get_concept("甲").short_definition == "甲是十天干第 1 位，分類為陽木。"
assert kb.get_concept("寅") == kb.get_concept("branch_yin")
assert kb.get_concept("寅").fact_ref.id == "yin"
assert "陽木" in kb.get_concept("寅").short_definition
assert [stem.char for stem in kb.get_hidden_stems("寅")] == ["甲", "丙", "戊"]

result = kb.get_ten_god("壬", "乙")
assert result.ten_god.name_zh == "傷官"
assert result == kb.get_ten_god("ren", "yi")
assert kb.get_ten_god("壬", "辛").ten_god.name_zh == "正印"

branch_result = kb.get_branch_ten_gods("壬", "戌")
assert branch_result == kb.get_branch_ten_gods("ren", "xu")
assert [(item.hidden_stem.char, item.ten_god_result.ten_god.name_zh)
        for item in branch_result.hidden_stem_results] == [
    ("戊", "七殺"), ("辛", "正印"), ("丁", "正財"),
]
```

藏干只存天干引用；完整屬性由基本資料取得。季節查詢保留資料來源與查詢步驟，
不宣稱四季可以唯一推導出完整藏干表。

個別地支說明只引用基本屬性，不帶入藏干、季節、組合或個人解讀。
`get_concept("yin")` 仍指陰，`get_concept("wu")` 仍指戊；
地支使用中文字或 `branch_` 前綴的說明 ID，避免不同集合的 ID 衝突。

v1.0 驗收包含完整引用、來源狀態保留、說明跟隨基本 YAML、欄位限制與既有功能回歸。
十神 v0.1 只接受 **Day Master Heavenly Stem × Target Heavenly Stem**，不接收地支或命盤；
v0.2 的 `get_branch_ten_gods()` 接受 **Day Master Heavenly Stem × Target Earthly Branch**。
日主由 caller 明確提供；藏干順序不是權重，也不產生地支的單一十神結論。
完整示例見 [天干十神](examples/ten_gods.py) 與 [地支藏干十神](examples/branch_ten_gods.py)。
十條規則採用使用者指定的 canonical implementation specification，歷史文獻依據仍標記
`requires_validation`。尚未加入排盤、日期換算、合沖刑害、個人命理解讀、資料庫、Web UI 或 LLM。
