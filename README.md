# Where Chinese Metaphysics Meets Science

目前專案是 **八字 Knowledge Engine**：建立機器可讀、可驗證、可追溯的八字知識庫。
**Layer 1 — Basic Elements：Status: v1.0 complete。**
陰陽、五行、十天干與十二地支均有基本資料、可查詢說明與來源／驗證狀態。
**Layer 3 — Four Pillars Structure v0.1：Status: implemented。**
接受已知四柱，列出日主、明干十神及藏干十神。Structural analysis only.

Layer 2 已有五行生剋、藏干、季節關聯與 **Ten Gods v0.2**：
保留 v0.1 天干對天干查詢，新增明確日主 × 地支藏干的有序展開，並回傳完整可追溯步驟。
**Sexagenary Cycle v0.1 已實作**：由天干／地支 order 產生 60 個合法配對，四柱分析先驗證每柱的循環成員資格。
**Pairwise Interaction Engine v0.1 已實作**：天干五合、地支六合／六沖，共 17 條 YAML 規則。
目前僅查詢明確的兩個成員；四柱自動掃描尚未實作。

```text
基礎元素 → 關係／組合規則 → 命盤結構 → 命理解讀
v1.0 完成  已有部分固定關係   v0.1 已實作  尚未實作
```

- [專案說明與文件導覽](bazi-knowledge-engine/README.md)
- [從零閱讀：陰陽、五行、天干、地支](bazi-knowledge-engine/docs/basic-elements.md)
- [四層架構與目前範圍](bazi-knowledge-engine/docs/architecture.md)
- [四柱結構 v0.1：已知四柱的結構分析](bazi-knowledge-engine/docs/four-pillars.md)
- [六十甲子與干支配對驗證](bazi-knowledge-engine/docs/sexagenary-cycle.md)
- [天干五合、地支六合／六沖查詢](bazi-knowledge-engine/docs/relationships.md#pairwise-interaction-engine-v01)
- [開發、API 與 YAML 參考](bazi-knowledge-engine/docs/development.md)

「可驗證」目前指資料、引用與程式行為可以檢查；文獻中的傳統對應不因此成為經科學驗證的因果關係。
資料與程式都位於 [bazi-knowledge-engine](bazi-knowledge-engine/)。
