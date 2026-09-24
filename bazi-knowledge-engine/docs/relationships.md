# 關係資料

[回文件導覽](../README.md) · [基本元素](basic-elements.md) · [API 參考](development.md)

本頁屬第二層。目前已有五行生剋、藏干、季節關聯，以及 Ten Gods Engine v0.1。
提供固定關係查詢與十神規則推導，還沒有通用推理引擎。

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

## 十神 v0.1

十神是以日主天干為參照，根據另一個天干與日主的五行關係及陰陽同異，
建立的十種關係分類。日主是本 API 的參照輸入，程式不自行辨識日柱。
十神不是目標天干的固定屬性；同一目標在不同日主下會得到不同結果。

**Status: v0.1 complete**。輸入範圍只有 **Day Master Heavenly Stem × Target Heavenly Stem**。
不接收地支、四柱或出生日期，也不從地支自動展開藏干。
這裡只說明關係名稱與推導，不賦予性格、職業、婚姻或吉凶含義。

| 日主視角 | 結構化五行分類 | 同陰陽 | 異陰陽 |
| --- | --- | --- | --- |
| 同我 | `same` | 比肩 | 劫財 |
| 我生 | `day_master_generates_target` | 食神 | 傷官 |
| 我剋 | `day_master_controls_target` | 偏財 | 正財 |
| 剋我 | `target_controls_day_master` | 七殺 | 正官 |
| 生我 | `target_generates_day_master` | 偏印 | 正印 |

這十條規則保存於 [ten_gods.yaml](../knowledge/ten_gods.yaml)，沒有列出 100 個天干配對。
七殺的 canonical name 為「七殺」，`aliases: [偏官]` 只是名稱資料，不改變匹配結果。
採用來源為使用者實作規格，全部規則仍標記 `requires_validation`；詳見[來源政策](sources.md)。

```python
from bazi_knowledge import KnowledgeBase

kb = KnowledgeBase()
result = kb.get_ten_god("壬", "乙")
assert result == kb.get_ten_god("ren", "yi")
assert result.ten_god.id == "shang_guan"
assert result.ten_god.name_zh == "傷官"
assert result.element_relation == "day_master_generates_target"
assert result.polarity_relation == "different"
assert kb.get_ten_god("壬", "辛").ten_god.name_zh == "正印"
```

「壬 + 乙」的完整五步推理：

```text
1. resolve_day_master：壬 = 陽水
   heavenly_stems:ren → elements:water, yin_yang:yang
2. resolve_target：乙 = 陰木
   heavenly_stems:yi → elements:wood, yin_yang:yin
3. element_relation：既有邊 {source: water, target: wood, relation: generates}
   水生木 → 我生（day_master_generates_target）
4. polarity_relation：yang / yin → different（陰陽不同）
5. ten_god_rule：day_master_generates_target + different
   rule_id: shang_guan → 傷官
```

「壬 + 辛」的完整五步推理：

```text
1. resolve_day_master：壬 = 陽水
   heavenly_stems:ren → elements:water, yin_yang:yang
2. resolve_target：辛 = 陰金
   heavenly_stems:xin → elements:metal, yin_yang:yin
3. element_relation：既有邊 {source: metal, target: water, relation: generates}
   金生水 → 生我（target_generates_day_master）
4. polarity_relation：yang / yin → different（陰陽不同）
5. ten_god_rule：target_generates_day_master + different
   rule_id: zheng_yin → 正印
```

每一步都有來源 ID；五行步驟保存實際使用的 `ElementRelation`，同五行時則為 null，
不虛構「same」五行邊。最終步驟保存匹配分類與 `rule_id`，可回查完整規則及其驗證狀態。
陰陽只比較兩個符號的屬性，沒有性別判斷。

原 `get_element_relation()` 繼續只查直接邊；新分類器會檢查正反方向。
自訂資料若讓不同五行間出現零條或多條候選邊，十神查詢明確報錯，不自行選擇優先順序。

驗收包含 100 種天干組合唯一命中，以及每個日主的十個目標恰好涵蓋十神各一次。
完整可執行 trace 示例見 [examples/ten_gods.py](../examples/ten_gods.py)。
Ten Gods v0.2 可再規劃日主與地支藏干的串接，本版尚未實作。
