# 來源與驗證邊界

[回文件導覽](../README.md) · [待辦清單](../TODO.md)

來源是各層共用的資料品質要求。名稱、基本分類、教學說明、傳統對應與推導前提
各自需要適當的依據，不能用一個來源替整筆記錄的所有內容背書。

## 來源政策

採用的基本分類與藏干表以使用者指定資料集為準。文獻提供指定範圍內的核對或概念背景；
遇到不同分類、順序、土的季節配屬或氣分類，不自行選一套覆蓋現有資料。

古籍使用公開文本轉錄；白話說明是本專案的教學改寫。
來源中的占斷、倫理或其他敘述不因引用同一篇文章就自動納入。
「文獻有記載」不等於已完成版本校勘、跨流派共識或現代科學驗證。

## 基本資料的來源代號

基本 YAML 檔首的代號對應下表。原基本資料的外部核對日期為 2026-09-22。

| 檔首代號 | 來源與採用範圍 |
| --- | --- |
| `phase1-spec` | 使用者原基本資料規格：陰陽、五行名稱與順序、生剋邊、十干分類及指定地支驗收值；測試保存驗收對應。 |
| `phase2-spec` | 使用者指定的十二地支藏干清單與順序；保存於 [hidden_stems.yaml](../knowledge/hidden_stems.yaml) 及 [test_hidden_stems.py](../tests/test_hidden_stems.py)。 |
| `hko-order` | [香港天文台：天干和地支](https://www.hko.gov.hk/tc/gts/time/stemsandbranches.htm)，核對干支名稱、順序。 |
| `ndl-elements` | [日本國立國會圖書館：干支①六十干支](https://www.ndl.go.jp/koyomi/chapter3/s1.html)，核對天干陰陽／五行及地支五行。 |
| `branch-polarity` | [《三命通會》論支元六合網路轉錄](https://sajumania.com/ebook/to01-05/to01-05-02-21.htm)，只核對段首地支陰陽分類，不匯入該章的關係規則。 |

**Requires source validation**：`branch-polarity` 尚須與指定古籍版本、頁碼覆核。
不同文獻若用「地支陰陽」表示不同分類，需先確認定義與範圍，不得覆寫目前欄位。
目前 `earthly_branches.yaml` 的陰陽指地支本身，五行指其本氣五行，不由藏干陰陽推導。

## 可查詢說明的來源登錄

完整 URL、章節定位、使用範圍及核對日期保存在
[sources.yaml](../knowledge/concepts/sources.yaml)。原說明來源記錄的核對日期為 2026-09-23；
新增登錄的 `branch_polarity` 沿用既有 2026-09-22 紀錄，沒有宣稱本次已重新完成外部版本核對。

| 來源 ID | 使用範圍 |
| --- | --- |
| `concept_spec` | 使用者對元素白話說明、傳統象徵及內容邊界的要求；不是古籍來源。 |
| `phase1_spec`、`phase2_spec` | 對應上述兩份使用者資料規格。 |
| `yijing_xici` | 《易傳》繫辭上第五、六章的陰陽傳統語境。 |
| `shangshu_hongfan` | 《尚書》洪範「一、五行」的名稱及曲直、炎上等描述。 |
| `huainan_tianwen` | 《淮南子》天文訓中的五行、方向、四時與相生記載；不據此指定唯一土季。 |
| `huainan_shize` | 《淮南子》時則訓中的孟仲季位置及季夏與土的記載。 |
| `sanming_renyuan` | 《三命通會》卷二〈論人元司事〉中藏干與四時的語境及不同說法；不驗證現有清單的全部順序或成因。 |
| `hko_order`、`ndl_elements` | 對應上述公開干支分類資料。 |
| `branch_polarity` | 對應既有 `branch-polarity`；把原文件中的待覆核來源登錄為可查詢引用。個別地支說明保留 `requires_validation`。 |
| `ten_gods_v01_spec` | 2026-09-24 使用者 Ten Gods v0.1 canonical implementation specification，涵蓋十條對應、名稱、方向定義、陰陽比較及七殺／偏官別名；不是古籍引文。 |

檔首代號使用連字號，程式來源 ID 使用底線，保留既有命名以避免破壞引用。
`phase1`／`phase2` 表示原始規格來源，不是現在的架構層名稱。
基本資料目前採檔案註解追溯；可查詢說明與季節資料則有逐項 `source_ids`。

## 來源狀態

| `source_status.value` | 意義 |
| --- | --- |
| `source_attested` | 已核對指定文本或使用者規格中的這項記載；不是對自然因果的驗證。 |
| `traditional_common` | 採用的傳統概念教學改寫，附所依據的參考及使用者規格。 |
| `requires_validation` | 版本、框架或推導前提尚未確認，不提升為固定規則。 |
| `derived_from_facts` | 由目前基本屬性產生的文字，例如甲的陰陽與五行介紹。 |

每筆傳統對應都有自己的來源狀態；不能以元素說明的整體狀態取代個別對應的狀態。
土的季夏記載與四季末／季節轉換說法分開保存，後者的整合與時間邊界仍待確認。

**Hidden stem weighting and qi classification require separate source validation.**
具體待核對項目集中於 [TODO](../TODO.md)，不以一般常識補成可執行的命理規則。

Layer 1 v1.0 complete 表示已完整提供基本元素資料、說明與來源狀態，
不表示所有來源已完成版本考據。產生或串接說明不會自動解除 `requires_validation`。

## Ten Gods v0.1 的採用依據

[十神規則](../knowledge/ten_gods.yaml) 直接採用本次使用者指定的十條 canonical mapping。
`ten_gods_v01_spec` 的 URL 為 null；`checked_on: 2026-09-24` 只指核對實作規格。
本次未搜尋或補入網路引用。完整對應、名稱與別名的歷史文獻版本均仍 **Requires source validation**。

每條規則保存 `source_ids` 與 `source_status: requires_validation`。
結果的 `ten_god` 保留原規則狀態；`sources` 提供 trace 所用來源的完整記錄。
基本天干來源由 YAML 的 `stem_source_ids` 指定，五行關係來源由 `element_source_ids` 指定，
二者均引用既有 registry，沒有另造五行對應表。
計算成功與 100 組測試通過表示實作符合採用規格，不代表完成歷史考證或證明自然因果。

## Ten Gods v0.2 的追溯

v0.2 組合既有藏干引用與 v0.1 規則，沒有新增傳統對應、規則來源或文獻引用。
地支 → 藏干的兩步 trace 使用 `get_concept("hidden_stems")` 原有來源 ID，
目前為 `phase2_spec`，其 locator 指向 `knowledge/hidden_stems.yaml`。
結果的 `hidden_stem_source_status` 保留這份藏干資料的狀態；目前 `source_attested`
僅指已核對使用者指定清單與順序。

每個子結果完整保留 v0.1 的五步 trace 與 `ten_god.source_status: requires_validation`。
外層 `sources` 合併這些步驟用到的既有來源，讓序列化結果可獨立追查來源記錄。
藏干清單已核對，不代表十神規則已完成歷史考據，也不會解除待驗證狀態。
120 組查詢通過表示資料串接符合規格，不驗證藏干權重、氣分類或命理因果。

## Four Pillars Structure v0.1 的組合約定

本版沿用使用者實作規格：四柱位置依 year／month／day／hour，日主取自 day.stem。
這些在本次實作中標記為 **implementation convention**；未新增歷史引文，也不宣稱已完成歷史文獻核對。
約定與適用範圍記錄於 [four-pillars.md](four-pillars.md)，不修改共用 SourceStatus 列舉。

外層六步 trace 記錄 caller 輸入、柱位置、基本物件解析及日主選取；
`source_ids` 為空 tuple，明確表示這些是本次輸入及程式組合約定，沒有引用文獻作為依據。
`chart:input`、`pillars:year` 等引用只在本次分析內有效，不是 YAML 知識 ID。
嵌套 Layer 2 trace 的來源 ID 保持完整，分析的 `sources` 合併其既有來源記錄。

計算或組合不解除十神的 `requires_validation`，不把藏干的 source_attested 擴大成權重或氣分類證明。
地支陰陽版本、土的季節整合、天干取象、藏干季節成因及權重仍維持原有待驗證邊界。
