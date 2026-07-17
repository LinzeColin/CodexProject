# 独立对抗复核 — ADP V0.2 P07 关注 /watchlist

复核者：独立 general-purpose skeptic（非实施者；**实施者不自签**）。共 **5 轮**，前 **4 轮全部 BLOCK**，且**每一条都属实、都是实施者的错**。

## 第一轮：BLOCK — 有界性分析只算了单条，漏了 ×WATCH_MAX
- 实施者把**循环写反**：T066 是 `for it in items: for w in watches`（**一遍**），实现成了**每条关注各扫一遍**（查询 + 正则）→ **×20**。
- `FS_DOCNUM_RE` 在中文正文上约 **0.041ms/行**（`[一-龥A-Za-z]{0,8}` 使 V8 在每个汉字位置都无法跳过；英文约 0.05ms/**1000** 行，差约 800 倍）。
- 实测 100 中文/900 英文 = **4.17ms/条 → ×20 = 83ms**；250 中文 = **207ms**。Workers **免费档 CPU = 10ms/次** → **约 3 条文号关注就打爆**，而页面写着上限 **20**。
- 复核指出这与 **P01-FACTSHEET 被 BLOCK 的是同一类**（「跑在请求路径会打爆 Worker CPU」），且**用行数放大抵消了 P01 自己 `slice()` 的先例**。

## 第二轮：BLOCK — 「你修的是症状，不是原理」
实施者只修了 `doc_number`，**把一模一样的 bug 原样留在 `keyword`**：`hay = (title+' '+summary).toLowerCase()` 是**只与条目有关**的工作，却写在 per-(item, watch) 内层 → 1000×20 = **2 万次重建**。`docs` 提出去了，`hay` **没提**。**乘数只是被挪了个位置，根本没消失。**

> **「Restoring T066's loop order doesn't fix anything by itself; hoisting item-only work out of the inner loop is what fixes it.」**

实测（复核）：20 条 keyword = **29.0ms**（全中文）／**7.95ms**（**纯英文也吃掉 80% 预算**）；**约 7 条越过 10ms**；成本**严格线性**于关注数（1/2/5/10/20 → 1.41/2.80/6.98/14.10/28.68）——**线性本身就是「每一对都在做活」的铁证**。

## 第三轮：BLOCK — 「修复 #3 亲手废掉了修复 #2」
实施者为「已读集可能被 LIMIT 截断」加了 `ORDER BY at DESC LIMIT 5000`，理由是「窗口 ≤ `WATCH_SCAN` 条，故最近的若干次已读必然覆盖窗口」。**这个前提是错的：`WATCH_SCAN` 限的是读取量，不是窗口。**

> **「You closed the hole in the write path and re-opened it in the read path. Fix #2 keeps the row; fix #3 refuses to read it.」**

构造性证据：**6001 行已读 → 重复通知 YES；400 行（LIMIT 不生效）→ no** —— **是 LIMIT 造成的**，与语料无关。触发条件是 ack 时序与发布时序**背离**：**未来日期的 `published_at`（政策生效日）永远排候选第 1 位，其 ack 时间却会老化出界 → 重复通知**——正是修复 #2 存在的那个洞。`ORDER BY` 另使该查询**丢了覆盖索引**（→ `USE TEMP B-TREE`，慢约 2.6×、每页 ×20）。

## 第四轮：BLOCK — known_gaps.md 把已被证伪的前提当依据写着
文档诚实性问题，非功能。已按事实重写（§3d/§3c#2 明确标注哪个修法是错的、错在哪）。

## 第五轮：CONFIRMED_SOUND
- **代码未被偷改**（密码学确认）：复核独立跑**自排除哈希**（`build_id`/`source_sha256` 归零后 sha256 整文件），复现 **`659d32fd39da`** 一致。
- 三个 nit（均已改）：§4 板块行标「约 25%」却用 4,500（实为 30%）→ 改为 **3,750** 并注明「均分 25% 只是记账口径，board1(arxiv+bioRxiv) 几乎必然远高于 25%」；§6 「**永不再成为候选**」是**写下来即为假**的绝对断言（下一条就是反例）→ 改为「在其重新进入窗口之前」；「实测」**过度声称出处** → 拆成 **实测 / 外推 / 推导** 三档。
- **一个真实缺口**：「the P07 evidence dir contains **only** known_gaps.md … the doc's 实测 numbers (83ms→0.92ms, the 6001-row counterexample → NO) currently have **no artifact backing them** in the package.」

## 实施者补缺口时**又踩了同一个坑**（自查，未等第六轮）
为补上述缺口写了 `test-results/watchlist_verify.mjs`（从**发货的** worker 抽真实函数，避免抄写漂移）。给负控跑了一遍：**把 `ORDER BY at DESC LIMIT 5000` 塞回去，测试照样绿（exit=0）**——D1 mock 的 `all()` **无视 SQL 文本**，不管 worker 问什么都把整个已读集递回去。**那条断言从来没在测 LIMIT，它测的是 mock。**

**这是本轮同一个病根的第 5 次**：T086 恒真、T040 canary 漏 `board_id`、P05 的死循环、P07 的 ×20 盲区，以及这次。已修（mock 忠实执行 `ORDER BY`/`LIMIT`，含 `?n` 绑定形态），负控现在承重：

| 负控 | 还原的缺陷 | 结果 |
|---|---|---|
| NC1 | 撤销 `hay` 提升（重新引入 ×WATCH_MAX 乘数） | 比值 **11.8×** → **FAIL (exit=1)** |
| NC2 | 撤销修复 #3（`ORDER BY at DESC LIMIT 5000`） | 未来日期条目**被重复通知** → **FAIL (exit=1)** |
| 发货代码 | —— | **PASS (exit=0)** |

## 复核确认无误的（皆为执行验证）
- **DIR-007 行数有界**：候选查询「时间窗 + LIMIT」双重有界；只用 `LIKE+LIMIT` 时匹配不到会为凑满 LIMIT **走完整个索引**（真实 schema 5 万行实测 **25.0ms**），加时间窗后计划为 `SEARCH cn_items USING INDEX idx_cn_items_recency (<expr>>?)`，无匹配仅 **1.51ms**。
- **`号` 预筛不可能丢弃真命中**：`FS_DOCNUM_RE` 两分支**都强制**含字面 `号`；复核**独立复跑 40 万串、280,494 次匹配、0 反例**；预筛测拼接串而 `fsFirst` 逐字段扫描——**拼接是字符超集，故无假阴性**。
- **剪枝谓词正确**：按**条目自身的窗口归属**（相关子查询按主键查 `cn_items`，**不用 join**，避开 D1 无 ANALYZE 的 join 顺序陷阱 = P02 被 BLOCK 的那一类）。
- **复核自己否决了自己的建议**：曾建议「用候选集成员资格把已读压到 ≤1000/条」，验证后**否决**——`worker_cloud.js:239` 的 `ON CONFLICT(id) DO UPDATE SET fetched_at=excluded.fetched_at` 会在重抓时抬高 `fetched_at`，`published_at` 为空的条目其 recency 即 `fetched_at` → 条目可**跌出前 1000 后又跳回第 1 位**，若已读行已被按候选集剪掉就会**重复通知**。
- 注入面：facet **白名单**、value 截断 80、**全部走 bind**；XSS 走既有 `esc/safeHref`，无新汇聚点。
- `runDaily` **不调用** `watchTables()`，故懒建表失败**不影响每日 cron**。

**结论：CONFIRMED_SOUND。实施者未自签。**
