# Sexagenary Cycle v0.1

[回文件導覽](../README.md) · [四柱結構](four-pillars.md) · [來源與驗證](sources.md)

**Layer 2 — 干支循環配對 · Status: implemented**

此模組定義單柱的合法輸入集合，由十天干與十二地支的既有 order 產生六十甲子。
第三層四柱分析先使用此驗證，再展開明干與藏干十神。

## 生成規則

```text
stems    = 天干依 order 排序
branches = 地支依 order 排序
length   = lcm(10, 12) = 60

對 i = 0 ... 59：
    stem   = stems[i % 10]
    branch = branches[i % 12]
```

不依 YAML 清單的實際存放次序，不按陰陽欄位直接判定，也不硬編碼 60 個配對。
產生的 `Pillar` 引用原 `HeavenlyStem`、`EarthlyBranch` 物件，不重存陰陽或五行。
起點為甲子（1），依序乙丑（2）、丙寅（3）、丁卯（4），終點為癸亥（60）。
再前進一步回到甲子；本版沒有提供 `next_pillar()`。

## API

```python
from bazi_knowledge import KnowledgeBase

kb = KnowledgeBase()
cycle = kb.generate_sexagenary_cycle()
assert len(cycle) == 60
assert cycle[0].stem.char + cycle[0].branch.char == "甲子"
assert cycle[-1].stem.char + cycle[-1].branch.char == "癸亥"

assert kb.is_valid_pillar("甲子") is True
assert kb.is_valid_pillar("甲丑") is False
assert kb.is_valid_pillar("乙子") is False
assert kb.is_valid_pillar("丙卯") is False
assert kb.get_sexagenary_index("甲子") == 1
assert kb.get_sexagenary_index("癸亥") == 60
```

`generate_sexagenary_cycle()` 回傳不可變的 `tuple[Pillar, ...]`。
查詢接受兩個中文字，不接受 ID、日期或 Pillar 物件，不自動修剪空白。
`is_valid_pillar()` 對任何非法字串回傳 False；`get_sexagenary_index()` 則拋出 ValueError。
兩者對非字串皆拋出 TypeError。序號從 1 起，Python tuple 的位置仍從 0 起。
亦可從 `bazi_knowledge` 匯入三個同名函式。

API 只需要現有基本知識，不讀取十神規則或 Concept 資料。原基礎 loader 的檔案要求保持不變。
自訂知識目錄的生成結果依該目錄的 order；本模組不拿內建字串表覆蓋自訂順序。

## 四柱整合

```python
result = kb.analyze_four_pillars(year="丙寅", month="辛卯", day="壬戌", hour="乙巳")
assert result.day_master.char == "壬"

# 拋出 ValueError: year: invalid sexagenary pillar '甲丑'
# kb.analyze_four_pillars(year="甲丑", month="辛卯", day="壬戌", hour="乙巳")
```

年／月／日／時全部先驗證，再進行任何十神分析。
`result.trace` 仍為原六步，各柱 lookup 的輸出新增 `sexagenary_cycle:index`，
以同一 KnowledgeBase 的循環查詢可解析該引用；嵌套十神 trace 與來源不變。

這次有意收緊四柱 API 的輸入契約：以前「字元存在但配對非法」可能通過，現在會拒絕。
合法四柱的模型、輸出與原 Layer 1／Ten Gods API 行為保持相容。
原 `Pillar` 是基本物件容器，沒有可存取 KnowledgeBase 的 validator；
循環成員資格在 KnowledgeBase API 邊界驗證，直接建立 Pydantic 容器不等於完成知識驗證。

各柱合法仍不保證年／月及日／時配柱相容，也不等於已驗證出生日期。
本版沒有生日轉換、曆法、權重、月令、合沖刑害或命理解讀。

## 驗證與來源邊界

測試涵蓋 60 個唯一配對、連續步進與首尾回環、每干出現 6 次與每支出現 5 次，
並窮舉全部 10 × 12 配對，驗證恰好 60 個合法、60 個非法。
60 個合法柱均測試放入四個柱位置；非法配對不會進入 Layer 2 分析。
修改暫存 YAML 清單次序不改變結果，修改 order 則會改變結果，確保計算使用資料。

公式採用本次使用者實作規格，未另作歷史文獻核對：Requires source validation。
原基本資料來源與待驗證狀態仍保留，沒有新增虛構引文。
目前完成六十甲子驗證；後續天干／地支互動及 Four Pillars v0.2 只列入 [roadmap](../TODO.md)。
