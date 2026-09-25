# Product Slice v0.1 — Streamlit Explainable Bazi MVP

[回文件導覽](../README.md) · [四柱模型](four-pillars.md) · [來源界線](sources.md)

**Status: implemented — Structural analysis only.**
這是可操作的已知四柱結構分析介面，將現有十神、藏干、六十甲子與 Pairwise 引擎組合呈現。
本次沒有新增傳統八字規則，不提供個人命理解讀。

## 啟動

Python 3.12+，於 `bazi-knowledge-engine/` 執行：

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[app]"
.venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

macOS／Linux 使用 `.venv/bin/python`。已啟用環境時可以使用：

```text
pip install -e ".[app]"
streamlit run streamlit_app.py
```

依終端顯示的 Local URL 開啟頁面，預設為 http://localhost:8501。
若埠已占用，可加 `--server.port 8502`；本機限定可加 `--server.address 127.0.0.1`。
終端按 Ctrl+C 停止服務。Streamlit 是 app optional dependency，純引擎不必安裝。
部署平台可使用相同 entrypoint 與安裝命令；本次未部署公開網站。

## 操作與畫面

預設輸入為 **丙寅 辛卯 壬戌 乙巳**。四欄分別為年、月、日、時柱，按「分析 · Analyze」提交。
介面只接受已知四柱，不接受出生日期。每柱由 engine 驗證字元與六十甲子成員資格。

- **日主**：壬、陽水，資料來自日柱天干。
- **四柱表**：年／月／日／時為四欄，列出天干、十神、地支、藏干、藏干十神。
- **命盤結構關係**：天干與地支分組，顯示左右柱位置及關係。
- **Why? 推理過程**：展開明干十神、日主選取、地支 → 藏干 → 十神的原始推理。
- **Knowledge Status**：呈現十神、藏干、Pairwise 的驗證狀態，下方可展開來源。

範例結果：

| 柱 | 明干十神／角色 | 藏干十神 |
| --- | --- | --- |
| 年：丙寅 | 丙 → 偏財 | 甲 → 食神；丙 → 偏財；戊 → 七殺 |
| 月：辛卯 | 辛 → 正印 | 乙 → 傷官 |
| 日：壬戌 | 壬 → 日主 | 戊 → 七殺；辛 → 正印；丁 → 正財 |
| 時：乙巳 | 乙 → 傷官 | 丙 → 偏財；戊 → 七殺；庚 → 偏印 |

偵測到 **年干丙 ↔ 月干辛：五合**、**月支卯 ↔ 日支戌：六合**。
關係區的依據可回查 rule ID 及原 source_status；不顯示合化或好壞推論。
如果某領域無命中，顯示「目前實作的 Pairwise Rule Set 中未偵測到關係。」

## 錯誤與狀態

輸入甲丑時，顯示「甲丑不是目前六十甲子中的合法干支配對。」並指出柱位置。
輸入 ABC 或甲甲時，顯示「請輸入一個天干 + 一個地支，例如：丙寅。」
錯誤由引擎的 PillarInputError 提供，UI 不另寫干支驗證。
資料缺失或內部失敗只顯示一般錯誤訊息，診斷留在伺服器日誌，不將 traceback 放到頁面。

成功結果保存在目前瀏覽器 session；新的提交失敗就清除舊結果。
表單尚未重新提交時仍是上次結果，結果頂端會列出實際分析的四柱，避免混淆。
沒有登入、使用者資料庫、跨 session 命盤保存或付費功能。

## 引擎與介面的分工

`analyze_four_pillars()` 先驗證四柱並取得原有結構，再掃描 6 組天干與 6 組地支配對。
`four_pillars.py` 只重用 `get_stem_relations()`／`get_branch_relations()`；
`ChartInteraction` 只補上位置，保留原 relation_result、trace 與來源。
`stem_interactions`／`branch_interactions` 僅包含命中規則，sources 合併原記錄。

`streamlit_app.py` 負責輸入、呼叫與 rendering。
`presentation.py` 只整理顯示資料與中文標籤，不包含任何配對表、十神或藏干判斷。
共同規則與結果模型集中在 models.py，以免 chart 與 interaction 模組循環匯入。

## 驗收與後續

```powershell
python -m pip install -e ".[app,dev]"
python -m pytest -q
```

測試涵蓋引擎六組掃描、位置、無命中、重複字元、來源、JSON、helper 與 Streamlit AppTest。
僅安裝 dev 時 AppTest 會 skipped；要驗收 MVP 請安裝 app,dev。
本次實際使用 Streamlit 1.64.0 驗收；一般安裝依 pyproject 的相容版本範圍解析。

十神及 Pairwise 仍 requires_validation。地支陰陽版本、土的季節整合、天干取象、
藏干季節成因／權重等原有待驗證事項未因此解除。
「可驗證」指資料、規則與程式行為可以追蹤與測試，不代表傳統說法已通過現代科學實證。

目前缺少出生日期排盤、刑害破／三合三會、月令旺衰、格局喜用及個人解讀。
先實際使用並收集回饋，再從 [TODO](../TODO.md) 的選項決定下一步；本次不繼續擴充。
