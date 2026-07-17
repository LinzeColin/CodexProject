# Known gaps · ADP-V02-P04 — board3 A0 官方原文接入每日 cron

## 1. ★本任务不翻开关（BOARD3_A0_ONLY 仍为 false）★
本次只交付**摄取**：board3 从「只有媒体报道」变成「媒体 + 官方原文并存」。
**没有**把媒体降为 discovery。理由不是保守，是硬事实：`BOARD3_A0_ONLY=true` 会让 `a0Board3Eligible` 把媒体全部降级，而在库里有足够 A0 官方原文**之前**翻开关会**清空 board3**。canary 现在直接给出这个前置条件：`safe_to_flip_flag = (board3_in_db_official_a0 > 0)`。
翻开关是**独立的、需真实覆盖度累积后**的一步（且 T039 的「14 日」本就要求真实日历时间）。

## 2. 诚实未接入的官方源（逐条实测，非推测）
| 源 | 实测 | 结论 |
|---|---|---|
| `gov-cn-fagui` (`/zhengce/fagui/`) | **HTTP 403** | 拦截，不接 |
| `nda-gov` (`nda.gov.cn`) | **仅 193 字节** JS 跳转空壳 | 无内容可解析；S3 适配器本就标 `live_blocked=True` |

★**我曾错误地把 `ndrc-gov` 也列入「不可接入」**★，理由写的是「整页无日期、新鲜链接只在弹窗里」。**独立复核证伪了这条**：该页有 **28 个 `<span>2026/07/16</span>` 斜杠格式日期**、**103 条（去重 81）发改委自有的 `t{YYYYMMDD}_` 政策链接**（解析后实测 200）。我的检验有两处错：只 grep 了 `YYYY-MM-DD` 短横线格式、且只看 gov.cn 链接。**已改正：ndrc-gov 现已作为第 4 个 A0 源真实接入**，且它产出的正是带**文号**的官方原文（如 `关于印发《海水淡化产业发展行动方案》的通知(发改环资〔2026〕1062号)`）。

## 3. 各源的性质差异（不可混为一谈）
- `stats-gov` / `cac-gov` / `ndrc-gov`：**及时**，列表页带真实日期（实测 2026-07-16/17）。
- `gov-cn-policy`（`/zhengce/xxgk/`）：**权威但不及时**——该页是「信息公开」**静态索引**，产出的是 2019/2020 的**基础性法规**（如《政府信息公开条例》）。它贡献的是**权威原文**这一轴，**不是**日更流。若把它当日更源看待即为自欺。
- **新版 gov.cn `/zhengce/content/YYYYMM/` 只有年月没有日 → `published_at` 留空（null），绝不编造「日」**；列表页也不提供日期。因此这类条目按 `COALESCE(published_at, fetched_at)` 以抓取日排序。

## 4. 只取列表页元数据，不抓正文
每源 1 个子请求（DIR-007）。因此 `summary` 为空、正文未入库。
影响：P01 的 factsheet 从 `title`+`summary` 抽取，A0 条目 `summary=''`，故**文号/关键数字只能从标题抽到**（好消息：官方标题本就常含文号，如 `发改环资〔2026〕1062号`，因此 P03 的「标识符匹配」对这些条目真的可用）。抓正文需每条 1 子请求，超预算，未做。

## 5. R2 原始字节归档：**A0 实际上没有被归档**（不声称）
cron 里 A0 走在 RSS 之后，而 `RAW_MAX_PER_RUN=3` 已被 RSS 抓取耗尽，故 A0 的原始字节**通常不会**写入 R2。
故本任务**不声称** A0 具备 R2 原文归档。（`/api/a0-canary` 现显式传 `sourceId=null` 以确保该只读端点不写任何东西——见下。）

## 5b. ★真实上线后才暴露：`stats-gov` 从边缘**间歇性**超时★
首次真实 runDaily：`a0_official=37 = gov-cn-policy 13 + cac-gov 4 + ndrc-gov 20`，**stats-gov 的 15 条没进来**，
`degraded:['a0:stats-gov']`、`result=降级`（诚实降级，未中断 cron —— 印证了失败隔离）。该次报 `TimeoutError`（`fetchFeedText` 的 15s AbortSignal）。
**但随后的边缘探测 stats-gov 又成功了（reachable=True, parsed=15）→ 所以这是间歇性超时，不是永久封锁。**
（此处刻意不夸大：不能因为观察到一次超时就声称「边缘不可达」。）
影响：某些日子 stats-gov 会缺席，由既有健康机制处理（连续 3 次失败→自动停用，3 天后自愈重试），无需特殊代码。
**真实每日可用源数需按真实日历累计观察**——与 T039 的诚实结论一致（真实 latency/coverage 需接 cron 后按真实运行暴露）。

## 5c. ★我自己的安全仪器曾恒真（已修，最危险的一个）★
canary 的 board3 查询漏选了 `board_id`，而 `a0Board3Eligible` 首行是 `if (it.board_id !== 'board3') return true`
→ 每一行都恒真通过 → 把 **105 条媒体误报成「官方 A0」**，并据此输出 **`safe_to_flip_flag: true`**。
**若有人信了它去翻开关，board3 会被清空**——正是这个 flag 存在的目的所要阻止的灾难。
**T040 原版 canary 同样漏选**，其 `board3_media_demoted_to_discovery: 0` 一直是**空跑**（从未真正检验过那道门）。
已修（补 `board_id`）；负控制证明该门现在真的会判：媒体行→false、官方行→true、漏 `board_id` 的行→true（复现 bug）。修复后线上实测：`总162 | 官方37 | 媒体125`，`safe_to_flip_flag` 随库内实际 A0 数变化。

## 6. 复核抓到的两个真实缺陷（已修，记录以免重犯）
1. **未鉴权写回归**：我把 canary 的裸 `fetch()` 换成 `fetchFeedText` 时，**静默继承了它的 R2 双写**——一个自称 `non_destructive: true`／「writes nothing」的**未鉴权**端点，冷启动每次命中会产生 **15 次持久化写**（3 R2 PUT + 3 `cn_artifacts` INSERT + 9 `cn_meta` 计数），并污染 `_rawWrites/_rawUsage`（只在 `runDaily` 重置）。**修复**：`fetchFeedText(s.list, env, null)`，命中其内部 `&& sourceId` 守卫。
2. **ndrc 排除理由事实错误**（见 §2）。
   两者都发生在一个「以诚实为前提」的改动上——故不接受「仅文档化」，均已实修。

## 7. 其它已知边界
- `kind: 'official'` 是新枚举值；`seedSources` 的清理只删 `kind='feed'`，因此若将来把某个 A0 源从 REGISTRY 移除，其历史行会**成为孤儿**（不会被自动清掉）。已知，未在本任务处理。
- `healthStmt(ok = items.length > 0)`：把「可达但解析出 0 条」判为失败。这是有意的——列表页改版会让解析静默归零，正应触发降级/自动停用（3 次失败停用、3 天后自愈重试），而不是假装健康。副作用：某源某天真的没有新内容且列表为空时会被误判一次（不致命，自愈机制覆盖）。
- 本任务**未**真实跑满一个 cron 周期的多日观测；真实每日产出/漏抓随真实运行暴露（与 T039 的诚实结论一致：真实 latency/coverage/cost 需接 cron 后按真实日历累计）。
