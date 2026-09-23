# 八字 Knowledge Engine

這是一個機器可讀、可驗證、可追溯的八字知識庫，目前還不是算命程式。
現在的重點是把**基礎元素的資料與白話說明整理完整**，讓沒有八字背景的人也能理解每個元素。

## 四層架構

```text
1. 基礎元素 ← 目前整理重點
   陰陽、五行、天干、地支：基本屬性＋白話說明
        ↓ 被引用
2. 關係／組合規則
   生剋、藏干；未來才加入十神、合沖刑害與條件式規則
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

第二層已有五行生剋、十二地支藏干，以及藏干與季節的關聯查詢。
它們目前是固定資料的查詢與串接，尚未實作通用 Rule Engine 或命盤組合分析。
四層是責任分工，不代表四層都已完成，也不要求依層號刪除已存在的功能。

## 文件導覽

| 想了解的事情 | 文件 |
| --- | --- |
| 陰陽、五行、每個天干和地支是什麼？ | [基礎元素入門](docs/basic-elements.md) |
| 四層如何分工？哪些已完成？ | [架構與目前範圍](docs/architecture.md) |
| 生剋、藏干、四季如何連接？ | [關係資料](docs/relationships.md) |
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
assert [stem.char for stem in kb.get_hidden_stems("寅")] == ["甲", "丙", "戊"]
```

藏干只存天干引用；完整屬性由基本資料取得。季節查詢保留資料來源與查詢步驟，
不宣稱四季可以唯一推導出完整藏干表。

本次文件整理沿用現有 YAML、模型與 API。尚未加入排盤、日期換算、十神、
合沖刑害、個人命理解讀、資料庫、Web UI 或 LLM。
