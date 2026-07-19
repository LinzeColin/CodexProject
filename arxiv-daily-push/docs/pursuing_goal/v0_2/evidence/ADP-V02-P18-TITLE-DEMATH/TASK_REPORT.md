# ADP-V02-P18 — 标题面 deMath + 不等式数学盲区

状态: **CONFIRMED_SOUND**（独立对抗复核 2 轮：R1 BLOCK 三项全属实并修正；R2 亲手重放破坏测试双 FAIL/还原一致、自造探针确认货币方向保守、确认零预签后 CONFIRMED_SOUND。实施者未自签）
release_mode: **PRODUCTION** — `9b978f42ee16` → `d0ebaee1f43c`（Version 714fbd7c-bca4-4cc0-950a-5156a5a67dcd；中间版 2b6b0fab7e59、4f550eb72818 见复核记录）

## 为什么（线上实测坐实才动手）
P17 审查者留「标题面未过 deMath」线索。先线上实测（verify-real-before-building）：`/search?q=entropy` 里
arxiv:1310.5162 标题裸呈现 **`$C1$-Genericity…`**，该条 `/item` `<h1>` 与浏览器 tab 同裸。坐实后动手。

## 做了什么（终版）
- **8 个标题相关面全过 deMath**：itemListHTML 列表行(0,110)、radar 列表行(0,90)、**真 /history 标题行(0,70)**、
  item/today `<h1>`、复习页 `<h1>`、tab `<title>` 渲染点、**itemPage tab 传参点**；`slice` 全在 deMath **之后**
  （先截断会把 `$` 对切成孤 `$`）。
- **不等式盲区 + 启发式收紧**：`$0 < m < d$` 曾没剥（`<>` 不在数学符集）。终版 `<>` 子句为
  「**≤24 字符且无 3+ 字母词**才算数学」——散文/货币语境必有整词，审查者对抗用例
  `prices moved from $5 < previous high and $9 later` 的**货币保留**，失败方向保守（宁留 `$` 不吃货币）。

## 复核记录（2 轮，如实）
**R1 BLOCK（判得对，两硬伤）**：
- **D1 声称面 ≠ 实际面**：我把 radar 列表行(1324) 误标成「history 列表行」，真 /history 标题行(1895, `s.title`)
  **没修**，复扫清单也从没扫过 /history——绿验证器在为贴错标签的断言背书。
- **D2 夹具空转**：不等式夹具 wantGone 写成预转义形态又被检查代码二次转义 → **永不匹配、零判别力**；
  我发给审查者的「符集破坏测试必 FAIL」是**未实跑的断言**，实跑结果与声称相反。
- 另 D3：「货币含 `<` 概率为零」是可证伪的过度声称（审查者当场构造出反例吃掉货币）。

**修正（本版全部落地）**：真 history 面 + tab 传参补修；夹具改**原始文本 + escLike 统一转义 +
expectNoDollar 硬断言**（结构性杜绝双重转义整类问题）；`<>` 启发式收紧（见上）；
**两项破坏测试本轮实跑**：去 `<>` 子句 → 不等式夹具 FAIL(exit1)、回退 history 面 → history pin FAIL(exit1)，
还原后字节一致、验证器 16✅。D3 改为如实的接受风险表述（见诚实边界）。

## 验证
- 验证器：7 夹具（含审查者对抗用例）+ 负控 + 9 静态钉（7 标题 pin），exit 0。
- 守卫：5/5；负控在 pre-fix 源触发 10 项；符集断言拆为三子句（基础类 + `[<>]` 子句 + 散文卫兵 `[A-Za-z]{3,}`）。
- **线上终验 6 页复扫**（1310.5162 / NRR / search / 首页 / **history** / radar）：裸 `$` 全 0；
  剥后 `C1-Genericity`、`0 < m < d` 保留；`/build.json=d0ebaee1f43c`。

## 诚实边界
- 只剥定界符不渲染数学；`$100$ vs $200$` 类无空白纯数字仍会剥（摘要里几乎总是数学）。
- **接受的残余风险（替代「概率为零」的过度声称）**：含 `<>` 且 ≤24 字符且恰好无 3+ 字母词的货币速记
  （如 `$5<x<10$` 表示价格带）理论上会被剥——真实语料未见；若观察到再收窄。方向已保守：有整词即保留。
- deepDivePrompt 里标题保留原始 `$`（喂模型的忠实原文，非展示面）。factsheet 用 title 只做抽取不直渲。

## 上线验证
`/build.json=d0ebaee1f43c`（=Version 714fbd7c）；6 页裸 `$` 全 0；`node --check` 过；P15/P16 验证器复跑不受影响。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：R1 BLOCK→修正→R2 CONFIRMED_SOUND；已部署 d0ebaee1f43c）
