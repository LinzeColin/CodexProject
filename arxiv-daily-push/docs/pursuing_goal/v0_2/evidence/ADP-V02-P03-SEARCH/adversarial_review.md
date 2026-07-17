# 独立对抗复核 — ADP V0.2 P03 增强搜索

复核者：独立 general-purpose skeptic（非实施者；实施者不自签）。方法：用捕获式 stub 驱动真实 `searchPage`、对真实 `schema_cloud.sql` 跑 `EXPLAIN QUERY PLAN`、用 `node-html-parser` 验 XSS（其首个正则探针出过假阳性，遂改用解析器复核）。

## 第一轮：BLOCK —— **诚实性**，非安全性

复核者明确：「Blocking on honesty, not on safety — the code itself is deployable.」

**安全面全部 PASS（执行验证）**：注入（8 种组合 + payload；唯一进入 SQL 文本的非字面量是 `?${binds.length}`，即数组长度，永不含用户数据；`board="b1' OR 1=1--"` 被 REGISTRY 白名单丢弃；`from="2026-01-01' OR '1'='1"` 被 `slice(0,10)` 截断后仍走绑定）；绑定编号 8 种组合均 `maxPlaceholder === binds.length` 且连续；**性能无回归**（无筛选计划与改前**逐字节相同**）；ReDoS 线性（最坏 1827 字符输入 0.012ms）；XSS 解析器验证 9 payload **零注入元素/处理器**；BUILD 自哈希一致；15/15 既有行为回归通过（legacy `/search?q=`、STUDY_JS、ChatGPT 链接、`%`/`_` 转义等）；`board5` 被正确排除（虚拟聚合板块，"全部"即 board5）。
重排的真实价值也被证实：一条 2020 年的精确匹配被从末位提到首位，越过 5 条更新的子串提及。

**三条诚实性缺陷：**
1. **空格归一化端到端为空**（我方自曝，被证实）：`国发〔2026〕12号→found=1`；`国发 〔2026〕 12号→found=0`；`国发〔2026〕12 号→found=0`。且 `normIdent` 的 ASCII 大小写折叠在召回层**冗余**——SQLite `LIKE` 本就大小写不敏感（实测）。
2. **★更严重、我方未提★ DOI 检索对 bioRxiv/medRxiv 完全失效**：`fetchBiorxiv`（worker_cloud.js:217-223）存 `id='biorxiv:'+doi`、`url='.../content/'+doi`，**DOI 从不进 title/summary**；而 SQL 只搜 title/summary，`itemIdentifiers()` 却抽 id/url —— **两个面不一致**。`itemIdentifiers` 能抽出 `10.1101/...`，`searchPage` 却 `找到 0 条`。页面偏偏承诺"输入…DOI 时精确命中会排在最前"。
3. **`精确命中` 徽章断言无法确立的事实**：board3 源全是新闻 RSS，行是**关于**文件的报道；库里没有原件时，一篇政策解读被标"精确命中 1 条"。贪婪前缀致判定不一致：`（国发〔2026〕12号）政策解读`→抽出 `国发〔2026〕12号`→假阳性命中；`转发国发〔2026〕12号文件`→抽出 `转发国发〔2026〕12号`→**真文件反被漏掉**。

判定：#2 是**功能缺陷**不是注意事项，#3 是**对用户作出虚假事实断言**，故不接受"仅文档化"。

## 第二轮：CONFIRMED_SOUND

- **#2 已解**：`q=10.1101/2024.05.01.592123` 现 `找到 1 条` 并置顶加徽章（旧的两列面返回 0）。**查询计划确未变**（复核跑了四种：旧2列无筛选 / 新4列无筛选 → **相同**；新4列+board → `SEARCH ... idx_cn_items_board_recency`；新4列+board+from+to → **日期条件亦被索引辅助**，属净改善）。
- **#3 已解**：`includes` 正确救回贪婪前缀场景（`转发国发〔2026〕12号` 现被置顶，`===` 会漏）。徽章现在是**代码能为每一行确立**的声称：只计"查询文本（模空白/大小写）出现在产品**本就抽取并在条目页标为文号**的那个标识符里"，**不声称该行是官方原件**。
- **`includes` 无假阳性**：`identLike` 门仍在且成立——`1`/`12`/`12号`/`x`/空串/`"   "`/`cancer`/`号`/`2026`/`CRISPR 基因编辑` 全部 `identLike=false`，零重排零徽章；普通词 `study` 不发徽章、recency 序不变。最危险的退化（空 `nq` 使 `includes('')` 恒真）**不可达**——门要求文号/DOI 前缀匹配，强制 `nq` 非空。宽而合法的 `10.1101/` 会置顶全部匹配行，但弱化后的措辞对每一行**仍字面为真**，且 hit/rest 分区稳定、组内 recency 保留。
- **#1 已解**：无条件承诺移除；文案点名真实检索面（标题/摘要/链接/ID == SQL 的四列）并给出条件。空格变体"记录而不声称"**可接受**——该变体下查询**并未**字面出现在标识符里，故无承诺被证伪；40 条上限已在页面内明示。

**复核者额外核验了 known_gaps 本身**（"过度声称的 known_gaps 本身就是诚实性缺陷"）：其 §2 数字**逐一复现**；查询计划声称复现；§3"board3 全是媒体源"**属实**（live REGISTRY = people-politics / people-finance / chinanews-scroll / sina-china-focus，`BOARD3_A0_ONLY=false`，无 A0 源上线）；并指出该文档**自曝**了 `normIdent` 大小写折叠冗余与"贪婪正则是容忍而非修好"——属**低报而非高报**。

**一处非阻塞 nit**：当 `exactCount === results.length` 时徽章说"N 条已置顶"但实际无一移动——空洞，但不虚假。

**终判：VERDICT: CONFIRMED_SOUND**
