# Known gaps · ADP-V02-P08 — 研究元数据增强（T063）

## 1. 交付的是 T063 中「线上数据能支撑的部分」，不是 T063 全部
T063 的 objective 是「完善论文**身份、作者、机构、版本和引用图**」。实际交付：

| T063 要求 | 本次 |
|---|---|
| 身份（DOI/OpenAlex id） | ✅ 确定性适配器从既有 id/url 解析 DOI，再查 OpenAlex |
| 引用图 | ⚠️ **只存 `cited_by_count` 一个标量**，不是「图」；不做引用关系、不做被引列表 |
| 作者 | ❌ **不做**。原本拉了 `authorships` 只为取 `.length`，实测一批 1.33MB、`JSON.parse` 2.48ms，为一个数字不值 → 已从 `select=` 去掉，`authors_n` 恒为 NULL（**留空，不臆造**） |
| 机构 | ❌ **不做**。需要 `authorships[].institutions`，同上，payload 代价大且当前无展示需求 |
| 版本 | ❌ **不做**。需要 S2 的 DocumentVersion 层（T025，未上线） |
| Crossref | ❌ **不接**。OpenAlex 已覆盖本场景，多接一个源 = 多一个外部子请求 + 多一套失败模式，不值 |

依赖的 `ADP-S5-P01-T059` **未上线**：本任务不依赖它的产物，直接从既有 `id/url` 解析 DOI。

## 2. ★验收 1「预印本/期刊不混淆」：只做到 OpenAlex 口径，不多说一个字★
判定规则：`w.type === 'preprint' || primary_location.source.type === 'repository'` → 预印本。
**必须是「或」不是「且」**（实测）：

| 源 | OpenAlex `type` | `source.type` | 判定 |
|---|---|---|---|
| arXiv | preprint | repository | 预印本 |
| bioRxiv / medRxiv | preprint | repository | 预印本 |
| **eLife** | **preprint** | **journal** | **预印本**（eLife 的 Reviewed Preprint 模式）|
| NEJM / Nature Comms / PLOS | article | journal | 发表于 |

（我最初的注释写「arXiv/bioRxiv/medRxiv/eLife 实测全部命中 preprint+repository」—— **那是假的**，eLife 的 source.type 是 journal。结论侥幸没错，但依据是假的，已改。）

## 3. ★绝不声称「研究论文」——因为 OpenAlex 自己分不清★
实测三个字段：

| DOI | 真实身份 | OpenAlex `type` | `is_paratext` | venue |
|---|---|---|---|---|
| `10.1038/d41586-026-02188-y` | **Nature 新闻报道** | `article` | `false` | Nature |
| `10.1073/iti2726123` | **PNAS「In This Issue」栏目** | `article` | `false` | PNAS |
| `10.1038/s41467-026-74639-z` | 真研究论文 | `article` | `false` | Nature Communications |

三者**完全无法区分**。故本实现**只如实转述 OpenAlex 的字段**（发表于 / 预印本 / 被引 / OA），
**不加任何「研究论文」之类的判断** —— 那个标签对前两行就是**假的**。
board2 的 RSS 里本来就混着大量新闻（`science-news`、`ieee-spectrum` 全是报道），这不是边缘情况。
**能做的诚实事**：转述来源与被引数；**不能做的**：替 OpenAlex 断言它没说的东西。

## 4. ★验收 2「增强失败不阻塞原始论文」★
`enrichMeta` 与 `attachMeta` **全程包在 try/catch 里，任何路径都不向外抛**：
- 网络抛异常 / HTTP 500 / JSON 畸形 → `counts.degraded.push('meta:…')`，cron 继续。
- `attachMeta` 遇到 D1 挂掉 → 原样返回条目、不挂 `_meta`，页面照常渲染。
- `enrichMeta` 跑在 `selectDaily` **之前**：若它抛了，会连当日精选一起废掉 —— 这正是它必须不抛的原因。
- 负控 nc2 / nc4 撤销这两个 catch 后套件立刻变红（见 `test-results/nc_results.txt`）。

## 5. DIR-007
- **外部子请求：+1**（20/50 → 21/50）。OpenAlex `filter=doi:a|b|c` 一批 = **一个**子请求。
  ★`META_BATCH=50` 是**我们自己的保守取值**，不是 API 上限★ —— 实测 OpenAlex 的 `doi` OR 上限是 **100**：
  `101` 个即报 `Maximum number of values exceeded for doi. Decrease values to 100 or below`。
  （原文写「其 OR 上限就是 50」是**假的**：把自己的选择说成 API 的强制约束。这条假话还写进了发货代码的注释。）
  取 50 的理由（是理由，不是约束）：重复 work 真实存在，留足 `per-page=200` 的余量。
  **★但这条理由本身也被复核削弱了，如实记下★**：实测各总体的重复率最高只到 **1.16x**
  （ADP 当晚 1.00x、任意真实 DOI 1.04x、arXiv-2015 1.03x、最差样本 1.16x），
  而 100 个 DOI 要到 **2.00x** 才会触到 200 的天花板 —— 比测到过的最高值还高 72%。
  所以「100 会逼近天花板」**没有任何实测支撑**：50 是**保守**，不是**被证明必需**。
  **代价**：约 600 条候选的存量按 50/晚 要 **12 晚**补完；取 100 则 6 晚，且数据支持取 100。
  这是可调的。留 50 是我的选择，但**不许再拿「API 不让」或「会撑爆 per-page」当挡箭牌**。
- **`per-page=200` 而不是 50**：同一个 DOI OpenAlex 可能回**多条** work，50 个 DOI 实测回过 **58 条**；`per-page=50` 会把真论文截掉并写成 `found=0`（「OpenAlex 不认识它」），而事实是**我们截断了自己的响应**（复核实测被截掉的是 FedAvg，5641 次引用）。200 是 OpenAlex 文档上限，实测有效。
- **D1**：候选查询**一板一条**（`board_id = ?1`），各自 `LIMIT META_SCAN(200)`。
  **写入上界 = `2 × META_SCAN` = 400 行**（400 INSERT + 2 条 SELECT + 1 条孤儿清理 DELETE + 1 条 `CREATE TABLE IF NOT EXISTS` = **404 次 D1 内部操作/次**，实测逐条计数确认）。
  ★这里我原本写「写入 ≤ 50 行」，是**错的，差 8 倍**★：`META_BATCH=50` 限的是**去重后的 DOI 数**，
  而写入循环是**按条目**展开的 —— §6 的广播规则把 1 个 DOI 写回**每一个**解析到它的条目。
  故上界由**候选数**决定，不是 DOI 数。实测反例：400 个候选只对应 **2 个**不同 DOI → **实发 400 条 INSERT**。
  （我自己的 §6 和 dedup 用例（1 个 DOI → 2 条写入）本来就摆在那儿，我却在 §5 写下了与之矛盾的数字。）
  **常态**约等于 DOI 数（≤ 50）—— 实测当晚真实批次重复率 0/50。
  为什么这个数字要紧：它不是给 5M/天 的行预算看的（400 行毫无压力），是给 **DIR-007 的
  「internal services ≈ 1000 次/invocation」天花板**看的 —— enrichMeta 与 `ingestAll`/`selectDaily`/
  `makeLesson`/prune/run-log **共享同一次 invocation 的这个额度**。把 404 写成 50，
  正好会误导下一个往这次 invocation 里加 D1 操作的人。
- **★「行数有界」的真正依据不是 LIMIT★**：`LIMIT` 限的是**返回行数**，不是扫描量。真正把这张表兜住的是
  `KEEP_PER_BOARD = 300` 的保留策略 —— board1+board2 合计约 600 行，故每晚候选读取约 600 行，
  对 D1 免费档 5M/天毫无压力。（我原注释写「LIMIT → 行数有界」是**假前提**，已改。）
  **但「600」不是硬上界**（如实说明）：prune 对被 `cn_reviews`/`cn_selections`/`cn_lessons` 引用的条目**豁免**
  （worker_cloud.js:392-394），受保护的行会越过 `KEEP_PER_BOARD` 累积。今天成立，估计每年上浮约 1k 行，
  十年后仍 < 5M/天 的 0.3%。—— 记在这里是因为「只看 KEEP_PER_BOARD、忽略豁免条款」与 §5 那个 8 倍错误
  **是同一种形状的推导**，只是量级小。
- **索引**：`board_id` 用**单值等值**而不是 `IN ('board1','board2')` —— 实测 `IN(2)` 会让计划放弃
  `idx_cn_items_board_recency` 并 `USE TEMP B-TREE FOR ORDER BY`（先全排序再 LIMIT）；单值时走
  `SEARCH cn_items USING INDEX idx_cn_items_board_recency (board_id=?)`，无临时排序。
- **CPU**：`metaDoi` 跑 200 行实测 0.03ms；去掉 `authorships` 后响应体大幅缩小。

## 6. ★dedup rules（两侧都要）★
- **请求侧**：多个条目可能解析到同一个 DOI（同一篇经不同 feed 进来）→ 按 DOI 归并成**一个**查询键，结果**广播回每个**条目。既不重复花子请求，也不漏条目。
- **响应侧**：OpenAlex 对**同一个 DOI 会回多条 work**（未合并的重复记录）。实测 `10.48550/arxiv.1506.01497` 回 **2 条，`cited_by` 分别是 18240 与 6274**。`env.DB.batch` 按序执行 = **最后一条赢** → 页面会把 **6274** 当事实展示，而 OpenAlex 自己的规范记录是 **18240**。
  「在互相冲突的记录之间随机挑一条当事实」正是本项目**明令不许**的事，故规则必须**确定**：
  **取 `cited_by_count` 最大者**（规范记录是合并后的，引用数最全），**并列时取 OpenAlex id 字典序最小者**。
  **重复率的三个数字各自属于不同总体，不要混读**（复核指出它们此前摆在一起像在互相打架）：
  | 总体 | 重复率 | 出处 |
  |---|---|---|
  | ADP 当晚真实批次（全是新论文） | **0/50** | 实施者实测 |
  | 50 个任意真实 DOI（跨年代混合） | 50 → **52~58** 条 work（约 4%~16%） | 复核第 1/5 轮实测，两次总体不同故数值不同 |
  | arXiv-2015 的 DOI | 约 **2.56%** | 复核第 1 轮实测 |
  规律是一致的：**越老的论文越可能有未合并的重复记录，新论文几乎没有**。故常态（ADP 只补最近的）重复极少，
  但 `per-page=200` 与响应侧去重仍然必需 —— 它们防的是尾部，不是常态。
  **残余风险（如实记录）**：这条规则只在**一对**真实重复上验证过。理论上一条被撤稿/paratext 的重复记录若引用数更高会胜出。
  影响面有界：代码只**逐字转述** OpenAlex 字段、从不合成标签，故最坏是**被引数字错**，不是**捏造身份**。

## 7. 截断判定「未知向安全侧倒」
`truncated = typeof meta.count !== 'number' || meta.count > results.length`。
拿不到 `meta.count` 就**无法**判断是否被截断 → 此时**绝不**写 `found=0`（否则又回到「把自己的截断栽赃成 OpenAlex 查不到」）。真实 OpenAlex **总是**回 `meta.count`（实测），故这是纵深防御，不是常态路径。

## 8. `found=0` 的重试语义
查过没查到 → 记 `found=0` + `enriched_at`，**`META_RETRY_DAYS = 7` 天后自动重试**（新预印本可能还没被 OpenAlex 索引）。
不记的话每晚都重查同一批查不到的；永久不重试的话新论文永远补不上。两头都不取。

## 9. ★证据本身被 BLOCK 了五次，五次都是我写下了假的依据★
这一栏留着，因为它比功能本身更重要：

| 轮次 | 复核抓到的 | 性质 |
|---|---|---|
| 1 | 假 D1 的 `all()` **无视 WHERE/ORDER BY/LIMIT** → 整条 SELECT 从没被测过；复核把 `board_id` 改成 `'nope'`、`LIMIT` 改成 999999、删掉 `ORDER BY`，套件三次都 PASS | 与 **P07 的 NC2 同一个病根**（mock 无视它自称在测的 SQL），仅隔一轮 |
| 2 | 我把 nc6 标成「承重」。真相：那版把 `LIMIT ?3` 改成 `LIMIT 999999`，留下没用上的绑定参数 → 它是因**参数个数不匹配**而红，不是 LIMIT 语义。**看见 exit=1 就写「承重」** | **假的覆盖声明** |
| 2 | 把 `USING COVERING INDEX` 当作发货查询的实测贴出。发货查询是 `SELECT id, url`，`url` 不在索引里，**不可能 covering** —— 那行输出来自另一条只 `SELECT id` 的探针 | **贴了别的查询的测量结果** |
| 3 | 我写「nc7 无法覆盖，ORDER BY 行为冗余」。复核**一行证伪**：给 fixture 加 `db.exec('ANALYZE')` → 计划从有序索引降级为 `SCAN cn_items`，「先补最新」当场垮成 **8/50** → ORDER BY **确实承重**。我不但状态标错，还在「修正」时把断言文案改得**离真相更远** | **把「我测不出来」写成「不可能测出来」** |
| 4 | 本文件 §5 写「写入 ≤ 50 行」。真实上界是 **`2 × META_SCAN` = 400**（≈404 次 D1 操作）—— `META_BATCH` 限的是 DOI 数，而写入是**按条目**展开的。**我自己的 §6 和 dedup 用例（1 DOI → 2 写）就在同一份文件里**，我却写下了与之矛盾的数字，且差的正是给 DIR-007「1000 次/invocation」天花板看的那个量级 | **同一份文件里自相矛盾** |

| 5 | 发货代码注释写 `// OpenAlex 单次 filter=doi 的上限 —— 50`。**实测上限是 100**（101 个即报 `Maximum number of values exceeded for doi. Decrease values to 100 or below`）。50 是**我自己的保守取值**，被我写成了 API 的强制约束 | **把自己的选择说成外部约束**（且这句假话进了发货代码） |

**病根始终是同一个**：*一个假前提被写下来，然后被信任*。
代码五轮下来**只在第 1 轮有真缺陷**；**后四轮全是证据造假**。
值得记住的是：第 2、3、4 轮里，**证伪我的材料一直就在我自己的包里**
（nc6 的红是参数错、covering 来自另一条探针、ANALYZE 一行、§6 与 §5 打架）——
不是我缺数据，是我**没去验自己写下的那句话**。

**fixture 用了 ANALYZE，而生产 D1 没有 ANALYZE** —— 即 fixture 比生产**更严格**。
这是**刻意**的：它测的是「这条 SQL 在 planner 不保序时是否仍正确」，而不是「今天的 D1 恰好怎么跑」。
靠「planner 碰巧保序」得到的正确性不是正确性，是运气。故此处不放松。

## 10. 其它边界
- 只补 `board1`/`board2`（论文板块）。board3/board4 是政策与机构公告，没有 DOI，`metaDoi` 对它们**返回 null**（弃权，不猜）。
- PLOS 的附件链接（`article/file?id=<doi>.PDF`）里的「DOI」是**资源名**，不是作品 DOI → `metaNotAsset()` 弃权。今天不可达（`parseFeed` 取每条 entry 的第一个链接），属纵深防御。
- 元数据徽章用**独立的 `title`** 标注出处（`OpenAlex 研究元数据·第三方来源·非原文抽取`），与「确定性抽取自原文」的徽章**分开** —— 证据来源不能混为一谈。
- `cn_item_meta` 的孤儿行（其 `cn_items` 已被 prune）在每次 cron **无条件**清理。
  （第一版把清理放在「有新条目要补」的分支里 → 稳态下**永远不跑**，而稳态恰恰就是孤儿堆积的时候。被我自己的测试当场抓到。）
- `env.DB.batch([q1,q2])` 读 SELECT 结果：这是**全仓唯一**一处用 `batch()` 跑 SELECT 的地方（其余 6 处都是写）。
  正确性依据是 Cloudflare 文档的 `D1Result[]` 契约（复核核对过），**没有仓内先例**。如实记录。
