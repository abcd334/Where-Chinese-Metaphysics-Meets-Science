# 關係資料

[回文件導覽](../README.md) · [基本元素](basic-elements.md) · [API 參考](development.md)

本頁屬第二層。目前提供固定關係的讀取與引用串接，還沒有通用推理引擎。

## 五行相生與相剋

相生、相剋是有方向的關係名稱；本階段不把「生」等同好事，或把「剋」等同壞事。

| 來源 | 所生的五行 | 所剋的五行 |
| --- | --- | --- |
| 木 | 火 | 土 |
| 火 | 土 | 金 |
| 土 | 金 | 水 |
| 金 | 水 | 木 |
| 水 | 木 | 火 |

資料存於[五行 YAML](../knowledge/五行/five_elements.yaml) 的 `relations`。
Python 讀取這些有向邊，不按五行順序推算。查詢水到木得到 `generates`，水到火得到 `controls`；
沒有直接邊時回傳 `None`，不增加反向、間接或同類關係。

## 地支到藏干

在目前採用的傳統資料表中，每個地支對應一組天干，稱為藏干。
這裡的「包含」指知識庫中的結構關係。

| 地支 | 藏干（保留指定順序） |
| --- | --- |
| 子 | 癸 |
| 丑 | 己、癸、辛 |
| 寅 | 甲、丙、戊 |
| 卯 | 乙 |
| 辰 | 戊、乙、癸 |
| 巳 | 丙、戊、庚 |
| 午 | 丁、己 |
| 未 | 己、丁、乙 |
| 申 | 庚、壬、戊 |
| 酉 | 辛 |
| 戌 | 戊、辛、丁 |
| 亥 | 壬、甲 |

採用依據是使用者指定的 canonical dataset，保存在[藏干 YAML](../knowledge/hidden_stems.yaml)。
順序只表示本資料集採用的排序，不表示百分比、力量或主氣／中氣／餘氣。
其他來源若有差異，先記錄來源與差異，不覆寫這張表。

```text
地支 戌
    ↓ branch_id: xu
藏干引用 [wu, xin, ding]
    ↓ 查詢既有天干資料
戊：陽土　辛：陰金　丁：陰火
```

藏干 YAML 只存 ID，陰陽與五行由第一層天干資料取得。
地支本身的陰陽不決定藏干陰陽，例如子本身屬陽，但藏干癸屬陰。

## 藏干與四季

現有資料記錄了以下傳統月序中的地支季節位置：

| 季節 | 孟（首段） | 仲（中段） | 季（末段） |
| --- | --- | --- | --- |
| 春 | 寅 | 卯 | 辰 |
| 夏 | 巳 | 午 | 未 |
| 秋 | 申 | 酉 | 戌 |
| 冬 | 亥 | 子 | 丑 |

對應及逐項來源存於[季節 YAML](../knowledge/concepts/seasons.yaml)。
這是傳統月序的符號關聯，不提供公曆、農曆或節氣時刻換算；
也不能只看年支、日支或時支就判定出生季節。

《三命通會》〈論人元司事〉有支中所藏與四時的論述，也有不同安排；
因此目前保留文獻關聯，不宣稱四季足以唯一生成本資料集的藏干表。
來源與適用範圍見[來源文件](sources.md)。

以辰為例，現有 API 串接的是：

```text
辰 ─→ 季春                 地支的季節位置
 └─→ 戊、乙、癸            既有藏干清單
       ├─ 戊 → 土 → 季節對應的不同說法，各自保留來源狀態
       ├─ 乙 → 木 → 春
       └─ 癸 → 水 → 冬
```

辰的基本五行為土、季節位置為季春、藏干包括不同五行，是三種不同關係。
串接中出現冬，不表示辰是冬季，也不產生旺衰或力量結論。
同樣地，知道寅對應春、木對應春，不能因此推出寅還藏丙、戊；
丙、戊的存在與順序仍來自指定藏干表。

```python
from bazi_knowledge import get_hidden_stem_season_context

context = get_hidden_stem_season_context("辰")
assert context.season.name_zh == "春"
assert context.branch_season.stage == "季"
assert context.derivation_kind == "reference_join"
assert [item.stem.char for item in context.hidden_stems] == ["戊", "乙", "癸"]
assert context.explanation.source_status.value == "requires_validation"
```

`trace` 列出 lookup／join、輸入引用、輸出引用與來源 ID，讓人能還原查詢過程。
待驗證的說明在串接後仍然待驗證；這個查詢不是藏干生成公式。

**Hidden stem weighting and qi classification require separate source validation.**
完整成因推導、權重與氣分類均列入[待辦清單](../TODO.md)，目前不實作。
