# 待辦與待驗證事項

[回文件導覽](README.md) · [架構](docs/architecture.md) · [來源政策](docs/sources.md)

## Layer 1 — Basic Elements

**Status: v1.0 complete**

- [x] 陰陽 2／2、五行 5／5、十干 10／10、十二支 12／12 的基本資料與個別說明可查詢。
- [x] 每項說明的 `fact_ref`、來源 ID 與驗證狀態可追溯。
- [x] 十二支沿用既有 Concept schema；基本分類只從 Basic Fact 取得。
- [x] 中文字與 `branch_` 說明 ID 可查詢；原 `yin`／`wu` 意義保持相容。
- [x] 完整覆蓋、非法引用、額外解讀欄位、內容邊界及既有功能均有測試。
- [x] README、架構、入門與開發文件同步。

Freeze 固定目前範圍與查詢契約，不把未驗證說法升格成已驗證知識。
後續文字可讀性回饋與文獻版本覆核屬維護工作；任何資料變更需更新來源、測試及文件。

## 待驗證清單

**Requires source validation**：下列問題不以模型一般知識補齊，亦不直接寫成可執行規則。

| 所屬內容 | 項目 | 處理邊界 |
| --- | --- | --- |
| 基礎元素 | 地支陰陽的轉錄版本 | `branch-polarity` 須與指定古籍版本及頁碼覆核；目前採用值保持不變。 |
| 基礎元素說明 | 土的季節配屬整合 | `get_concept("earth")` 分開保留季夏記載與季節轉換說法，不合併成時間或力量公式。 |
| 基礎元素說明 | 天干具體物象 | `get_concept("stem_imagery")` 保留待核對狀態；甲／大樹等提案不加入固定屬性。 |
| 未採用的地支擴充 | 動物、月份、時辰、方位 | Future source validation：先確認來源及所屬層級，目前不加入個別地支說明。 |
| 關係規則 | 從四季生成完整藏干表 | `get_concept("hidden_stems_seasons")` 只保留關聯；完整推導需額外前提、版本與反例，不改指定清單。 |
| 關係規則 | 藏干權重與氣分類 | Hidden stem weighting and qi classification require separate source validation. |
| 關係規則 | 十神完整對應、名稱與七殺／偏官別名 | `ten_gods_v01_spec` 為使用者實作規格；十條規則均標記 `requires_validation`，尚未指定歷史文獻版本。 |

寅對應春、木對應春，不能單靠這兩項資料推出寅還藏丙與戊，更不能決定順序或比例。
現有 API 的藏干來自指定清單。《三命通會》〈論人元司事〉並列不同安排；
不可挑選其中一段後宣稱已證明整張表。

## Layer 2 — Ten Gods Engine v0.1

- [x] 十條 YAML 規則，覆蓋五種五行關係 × 兩種陰陽關係。
- [x] 天干中文／ID 查詢，回傳結構化結果與五步 trace。
- [x] 100 種組合全部唯一 resolve，每個日主得到十神各一次。
- [x] 非法規則、來源引用、方向衝突及舊 API 回歸測試。
- [x] 所有規則保留 `requires_validation`，不加入個人解讀。

既有五行生剋、藏干、季節關聯及 v0.1 查詢契約繼續保留。

## Layer 2 — Ten Gods Engine v0.2

- [x] `get_branch_ten_gods(day_master, branch)` 支援中文與各自集合的 ID。
- [x] 串接 `get_hidden_stems()` 與 `get_ten_god()`，保留藏干原順序及 v0.1 結果物件。
- [x] 地支 → 藏干 reference → 天干 → 五行／陰陽 → 規則的完整追溯。
- [x] 藏干來源狀態及各十神規則的待驗證狀態分別保留。
- [x] 120 個日主／地支組合、280 個藏干十神結果與 v0.1 一致；錯誤、順序及來源均有測試。
- [x] 新增範例與文件；全部既有測試繼續通過。

Ten Gods v0.2 的明確日主輸入契約保持不變；四柱組合由第三層處理。

## Layer 3 — Four Pillars Structure v0.1

**Status: implemented — Structural analysis only.**

- [x] 四個必要的中文干支字串，先驗證一干一支及 Layer 1 引用。
- [x] 固定 year／month／day／hour 順序，自動以日柱天干為日主。
- [x] 年、月、時干重用 `get_ten_god()`；日干標示 `role: day_master`。
- [x] 四支一致呼叫 `get_branch_ten_gods()`，保留藏干順序、完整子結果及來源狀態。
- [x] `Pillar`／`FourPillars`／分析模型可序列化，外層 trace 連到既有 Layer 2 trace。
- [x] 指定案例、非法輸入、日主切換、重複柱、物件重用、來源及舊 API 回歸測試。
- [x] 新增四柱文件與可執行範例，同步 README／架構／開發參考。

四柱位置與日主選取採本次使用者規格的 implementation convention，沒有新增古籍引文。
實作僅驗證結構，不驗證六十甲子配對、年／月／日時配柱或日期可實現性。
本次完成 v0.1 後停止；不加入權重、月令、旺衰、干支互動或命理解讀。

## 後續建議：尚未開始的工作

下一步可先核對十神名稱與對應的指定文獻版本，記錄差異及適用範圍。
Four Pillars v0.2 可另行規劃明確格式的批次輸入／匯出，以及逐柱定位的驗證錯誤報告。
其他合沖刑害與條件式規則另行規劃；第四層命理解讀仍未實作。
