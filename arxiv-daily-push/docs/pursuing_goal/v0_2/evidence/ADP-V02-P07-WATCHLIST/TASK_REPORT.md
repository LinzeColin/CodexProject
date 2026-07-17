# ADP V0.2 生产集成 · P07 — 关注 /watchlist（PRODUCTION DEPLOY）

## 为什么有这一批
`NAV` 里 `/watchlist` 一直在，但 S6 的 T066 (`tools/watchlist_digest.py`) 建好后**从未接进线上**（NOT_DEPLOYED）——这正是 Owner 说「网页没有明显变化」的同一个病根。P07 把「关注」变成线上真能用的东西：**盯住一个文号 / 一个板块 / 一个关键词，只看还没看过的新条目。**

## 交付
1. **`/watchlist` 真页面** + `/api/watch/{add,del,ack}`：三个 facet（`doc_number` / `board` / `keyword`），上限 20 条。
2. **`watchDigest()` 一次共享窗口扫描**（30 天 + `LIMIT 1000` 双重有界）→ `for it in items: for w in watches`，与 T066 的循环序一致。
3. **`doc_number` 复用 P01 的确定性抽取器**（`FS_DOCNUM_RE`），与 P03「标识符匹配」同口径；board3 的 A0 官方原文标题常带文号（如 `发改环资〔2026〕1062号`），故这一条对**官方原文**真正可用。
4. **可重入**：ack 记 `(watch_id,item_id)`，再看即零未读；`cn_watch_seen` 按**条目的窗口归属**剪枝，不是按 ack 时间。

## 我自己先抓到的（未等复核）
在为第五次复核指出的缺口补测试时，我给负控跑了一遍：**把 `ORDER BY at DESC LIMIT 5000` 塞回去，测试照样绿**。我的 D1 mock 的 `all()` **无视 SQL 文本**，不管 worker 问什么都把整个已读集递回去——**那条「反例→NO」的断言从来没在测 LIMIT，它测的是我的 mock**。已修（mock 忠实执行 `ORDER BY`/`LIMIT`），NC2 现在如实 FAIL。详见 known_gaps §3e。

## 独立对抗复核：四次 BLOCK，全部属实，全部是我的错
| # | 复核抓到的 | 根因 |
|---|---|---|
| 1 | 有界性分析**只算了单条**，漏了 ×20 | 循环写反：每条关注各扫一遍 → 20 条文号关注 **83ms** vs Free 档 **10ms/次** |
| 2 | 修了 `doc_number`，**把一模一样的 bug 留在 `keyword`** | `hay` 仍在 per-(item,watch) 内层 → 2 万次重建 → **29.0ms**；乘数只是被挪了位置 |
| 3 | **我的修复 #3 亲手废掉了我的修复 #2** | 假前提：「`WATCH_SCAN` 限的是窗口」。它限的是**读取量**。`ORDER BY at DESC LIMIT 5000` 截掉**最早 ack** 的行 → 未来日期的政策（生效日）永远排候选第 1、ack 却老化出界 → **重复通知** |
| 4 | known_gaps.md 把**已被证伪的前提**当依据写了下来 | 同上 |

复核第 2 次的原话是这一整轮最该记住的一句：
> **「Restoring T066's loop order doesn't fix anything by itself; hoisting item-only work out of the inner loop is what fixes it.」**

**按原理修，不是打补丁**：内层循环里不得有任何「只与条目有关」或「只与关注有关」的计算——`hay` 每条目一次、`w._nv` 每关注一次，`watchMatches` 现在**零** per-pair 计算；`ORDER BY`+`LIMIT` **整个删掉**，使截断**构造上不可能**，有界性交回给已被验证正确的按窗口剪枝。

第五次复核 **CONFIRMED_SOUND**，并用**自排除哈希**独立确认代码未被偷改（复现 `659d32fd39da` 一致）。

## 验收（`test-results/`，可复跑，负控承重）
`watchlist_verify.mjs` 从**发货的** `worker_cloud.js` 抽出真实函数再断言（不重打代码，避免抄写漂移）：

- **CPU**（Workers Free = 10ms/次）：20 keyword@1000 中文 **1.16ms**、纯英文 **0.61ms**、20 doc_number@1000 中文 **2.13ms**；1→20 条关注 **0.33→1.16ms（3.6×，非 20×）**。
- **正确性**：keyword 命中 1000、board 精确 1000、doc `国发〔2026〕7号` **精确 1 条**、大小写不敏感、`%` 为字面量；**NC**：无文号的行不被 doc_number 命中。
- **可重入**：首看全未读 → ack 后**零未读** → 新条目仍会浮出。
- **复核的反例**：6001 行已读 + 未来日期政策（ack 最早）→ **不重复通知**。
- **`号` 预筛**：20 万串模糊测试，156 次匹配、**0 次不含 `号`** → 预筛不可能丢弃真命中。

| 负控 | 还原的缺陷 | 结果 |
|---|---|---|
| NC1 | 撤销 `hay` 提升 | 比值 **11.8×** → **FAIL (exit=1)** |
| NC2 | 撤销修复 #3（`ORDER BY at DESC LIMIT 5000`） | 反例**被重复通知** → **FAIL (exit=1)** |
| 发货代码 | —— | **PASS (exit=0)** |

## 诚实边界
见 `known_gaps.md`：**这不是 T066，是它在线上数据能支撑的诚实子集**——`topic/agency/region/entity` 需要 S5 实体解析（未上线），**不臆造这些字段**；`keyword` 是 ADP-V02 追加、**不是** T066 的 facet；**只报新条目，不做「内容实质变化」**（需 T026 版本层，未上线），页面明写；无 T066 的 silence signal；30 天 / 1000 条窗口的语义代价（更早的匹配不列出）页面明写且直接插值、不会与代码漂移；**已读读取是候选扫描的约 300 倍，它才是 D1 配额的主导项**（只烧配额、不破坏正确性），关注变多变宽时这里是第一个要优化的地方。

release_mode: **PRODUCTION**。未自签。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
