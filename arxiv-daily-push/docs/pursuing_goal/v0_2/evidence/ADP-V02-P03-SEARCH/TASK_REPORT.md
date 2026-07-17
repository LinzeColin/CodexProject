# ADP V0.2 生产集成 · P03 — 增强搜索（PRODUCTION DEPLOY）

## 做了什么
把 S5-P02-T060 中**线上数据真能支撑**的部分接进 `/search`：
- **结构化筛选**：板块（REGISTRY 白名单）+ 日期范围（`YYYY-MM-DD` 正则门），GET 表单。
- **标识符置顶**：查询形如文号/DOI 时，把"查询出现在该行抽出的标识符里"的条目排到最前（复用 P01 的抽取器，对已召回的 ≤40 行在 worker 内重排，**零额外 DB 成本**）。
- **检索面补齐 `id`/`url`**（见下，修复真实缺陷）。

## 独立对抗复核：BLOCK（**诚实性**，非安全性）——三条全是真的
复核者明确表示"代码本身可部署"，但**页面在承诺它做不到的事**：

1. **我自己举报并被证实**：文号带空格时 SQL `LIKE` 返回 **0 行**，重排器根本不会运行——"归一化"端到端是空的。实测 `国发〔2026〕12号→1`、`国发 〔2026〕 12号→0`、`国发〔2026〕12 号→0`。
2. **★我没发现、更严重★**：`fetchBiorxiv` 存的是 `id='biorxiv:'+doi`、`url='.../content/'+doi`，**DOI 从不进 title/summary**；而我的 SQL 只搜 title/summary，抽取器却读 id/url——**检索面与抽取面不一致**。结果：输入 bioRxiv DOI，页面承诺置顶，实际**一条都搜不到**（board1 主力源）。
3. **徽章在断言它无法确立的事实**：board3 数据源**全是媒体新闻 RSS**（人民网/中新网/新浪），行是**关于**文件的报道/解读，**不是文件本身**；一篇政策解读被标成"精确命中"。且贪婪前缀 `[一-龥A-Za-z]{0,8}` 会吞入上文，导致语义相同的行得到相反判定。

## 修复（全部采纳）
- **①检索面对齐**：`WHERE (title|summary|id|url LIKE ?1 ESCAPE '\')` —— **同一个绑定 ?1、无新参数**。复核用 `EXPLAIN QUERY PLAN` 实测：**查询计划逐字节不变**（`LIKE %x%` 本就不可走索引），零成本。bioRxiv DOI 场景由 **0 条 → 命中并置顶**。
- **②语义可证**：`===` 改 `includes`（容忍抽取吞入的前缀，使「转发国发〔2026〕12号」这类**真文件**不再漏掉）；徽章 `精确命中` → **`标识符匹配`**——只声称"查询出现在该行抽出的标识符里"，**不声称该行是官方原件**。
- **③文案诚实化**：移除"输入文号或 DOI 时，精确命中会排在最前"的**无条件承诺**，改为"在标题、摘要、链接与 ID 中检索……若查询出现在某条的文号／DOI 这类标识符里，该条会被置顶"（所述四列 == SQL 实际四列）。

复核复验：`includes` **不引入假阳性**（`identLike` 门仍在；`1`/`12`/`12号`/`x`/空串/`cancer` 等一律不重排不发徽章；空 `nq` 的退化路径**不可达**，因为门要求文号/DOI 前缀匹配）。**终判 CONFIRMED_SOUND**。

## 净收益（不只是没变差）
- 无筛选：`SCAN cn_items USING INDEX idx_cn_items_recency` —— 与**改动前逐字节一致**（未变差）。
- 给出板块：收窄为 `SEARCH cn_items USING INDEX idx_cn_items_board_recency (board_id=?)`；加日期范围后复核实测**日期条件亦被索引辅助** → **净改善**。

## 部署与验证
- BUILD `e301f8a4c7d8 -> e78306049663`；部署 adp-cloud version `8a6ef433-b93d-4730-855d-d15a2b08bc10`（绑定 + cron 保留）；回滚 `wrangler versions deploy bfa3ac49-31a2-426c-8aaf-b0c33caf60d1`。
- 实时验证（test-results/deploy_verify.txt，PASS）：build.json 一致；**12 条路由全 200**（含 `?board=` / `?from=&to=` 组合）；**六主题 6/6**；筛选表单渲染；**页面无「精确命中」过度声称**；**P01 芯片（60）与 P02 /library 均未回归**。
- T078 视觉差分 gate：**零视觉契约元素移动**。

## 诚实边界
见 `known_gaps.md`。要点：这**不是** T060 的 O(1) 精确查找（只是对 ≤40 行重排）；空格变体端到端不成立；agency/region/status facet 无对应列未做；**「标识符匹配」升级为真正的"权威原文命中"，取决于 P04 把 board3 接上 A0 官方原文**。复核者额外核验了 known_gaps 本身**未夸大**（其数字与查询计划均可复现，且自曝 `normIdent` 的大小写折叠在召回层冗余）。

release_mode: **PRODUCTION**。未自签；独立复核 CONFIRMED_SOUND。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
