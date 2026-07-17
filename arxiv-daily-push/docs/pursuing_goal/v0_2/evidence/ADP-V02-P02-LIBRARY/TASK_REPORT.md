# ADP V0.2 生产集成 · P02 — 知识库 /library 上线（PRODUCTION DEPLOY）

## 背景
`/library` 此前线上返回 **404**——S5-P04-T067 的 Library 一直是 NOT_DEPLOYED 的独立工具。本任务把它作为**只读视图**接进线上，让"学过的东西"成为可浏览、可回溯的长期资产，而不是只存在于"今天"。

## 做了什么
- 新增 `libraryPage(env, params)`：数据只来自线上 **`cn_reviews` ⨝ `cn_items`**（你学过／在复习的条目）。
  - 顶部：总条数 + **按板块**、**按证据态** 的分面计数芯片（可点击筛选，`?board=` / `?state=`）。
  - 列表：标题 → 条目页、板块、发布日、**原文**链接、证据态、复习次数、下次复习日，并复用 **P01 的关键事实芯片**（DOI/文号/关键数字/作者）。
- 导航新增「知识库」入口；路由 `/library`（精确匹配，不遮蔽 `/item/`、`/board/`）。
- **不新增 D1 表、不改每日流水线、不改 hero/动效/主题**。

## 诚实边界（未做，且不假装做了）
T067 的完整范围是 **Library + 笔记 + 全 provenance 导出**。其导出规则是硬性的：`PROVENANCE_FIELDS = (source_url, version, fetched_at, claim_evidence, license)`，**任一字段缺失即拒绝导出**。线上 `cn_items` 只能提供 `source_url` 与 `fetched_at`；`version` / `license` 属于 S2 版本层，**尚未上线**。因此：
- 本次**只交付 Library 视图**，**不交付笔记与导出**——若强行导出，按 T067 规则本就会被拒绝；臆造 provenance 更是禁止的。
- 笔记需要新增 `cn_notes` 表 + 写入端点；导出需要 S2 版本层先上线。二者留待后续 phase。
- 页面文案不提"笔记/版本/许可/导出"，不作任何无法由线上数据证明的声称。

## 独立对抗复核抓到的真实缺陷（已修）
复核者 **BLOCK**：两条查询都会 **全表 SCAN `cn_items`**——D1 不带 `ANALYZE` 统计，规划器从大表驱动 join，`SEARCH r` 逐行探测。实测（`cn_reviews` 固定 500 行，只变 `cn_items`）：1k→0.4/0.8ms、20k→4.0/4.6ms、**200k→33.1/39.4ms**，即**每次页面访问读 ≈2×|cn_items| 行**；200k 时约 40 万行/次，对 D1 免费档 **5M 行/天**（还要和每日 cron 及所有页面共享）意味着**十几次浏览就能耗尽当天预算**——直接违反 Owner 在 T087 签署的 **$0/mo 免费档基线（DIR-007）**，并且**回归了已上线的 T083**（T083 的交付物正是消除热路径全表扫描）。

**修复**：`JOIN` → **`CROSS JOIN`**（SQLite 将左表钉为外层循环，经 `ON` 仍是内连接，结果集不变）。
**验证（含载重负控制）**：
- 修复后计划：`SCAN r` + `SEARCH i USING INDEX sqlite_autoindex_cn_items_1 (id=?)` —— `cn_items` **只被索引查找，永不扫描**。
- 负控制（改回普通 `JOIN`）：`SCAN i USING COVERING INDEX idx_cn_items_board_recency` —— 证明该检查**不是恒真空跑**。
- 复核者复测：STATS 33.4ms→0.40ms（82×）、LIST 39.0ms→0.81ms（48×），四种筛选组合结果**逐字节一致**。

同时修掉一个次要问题：证据态为空时的 `—` 分面芯片会展示一个**无法被筛选到**的计数，已不再渲染该芯片。

## 部署与验证
- BUILD：`0864030f7dc8 -> e301f8a4c7d8`（build_id == source_sha256[:12]）。
- **六主题/动效契约未破**：T078 gate `decision: PASS, blocked_on: []`（NAV 项与页面正文不属冻结的 theme/motion 契约面）。
- 实时验证见 `test-results/deploy_verify.txt`。回滚：`wrangler versions deploy <上一版本>`。

release_mode: **PRODUCTION**。未自签；独立复核 CONFIRMED_SOUND（adversarial_review.md）。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
