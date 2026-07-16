# TASK_REPORT · ADP-S7-P03-T083｜优化 Bundle、D1 查询、流式布局和长列表

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P03-T083（Stage S7 / S7-P03 RUM、CWV、动效与数据性能，size M）
- **release_mode**: NOT_DEPLOYED（改 schema+worker 查询，重算 BUILD `0cb3acee6bf3`→`d1dfcb3b7447`，不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P03-T081

## 6 个前置问题
1. **哪个 D1 查询最慢？** — 热路径按 `COALESCE(published_at,fetched_at) DESC` 取前 N（today/radar/浏览/往期/搜索/候选池），旧 `fetched_at` 索引表达式不匹配 → **全表扫 cn_items + 临时 B-tree 排序**。cn_lessons(item_id)/cn_reviews(due_at)/cn_events(kind,at) 无索引。
2. **怎样降 rows scanned + p95？** — 加 5 索引（含 recency 表达式索引带 `id DESC` 尾键）；查询由 SCAN+TEMP-B-TREE → 索引顺序 SEARCH，只读 LIMIT 行（无临时排序）。
3. **怎样「无布局跳动回归」？** — 应用**服务端整页渲染**（无异步内容加载 → 无 CLS）；**六主题视觉/动效合同逐字节不变**（查询改在页面体函数，非合同哈希）；recency 顺序单调。
4. **★复核发现的真 hole 与修复★** — 独立 skeptic 证：仅加索引（无并列破除键）会在**跨族并列**（一行 recency 来自 published、另一来自 fetched，COALESCE 相等）时**改变分页成员/顺序**（board/browse），且**验证器有盲点**（旧合成数据把 published 放 2016、fetched 放 2026 → 跨族并列不可能构造，检查空过）。**修复=给 8 条 recency 显示查询加确定性全序破除键 `, id DESC`（与既有淘汰查询 line 352 一致）+ 索引尾键含 id DESC**→ 全序确定、索引完全服务（无临时排序）、**OFFSET 分页不跳/不重**；验证器合成数据现含跨族并列，盲点关闭。
5. **CWV 达标？** — 不声称（NOT_DEPLOYED 无字段数据，遵 T081「无数据不声称达标」）。
6. **NOT_DEPLOYED？** — 索引 DDL 进 schema、查询改在 worker；部署时索引 `wrangler d1 execute` 幂等建；未部署即未建。

## 交付物
- **5 D1 性能索引**（schema_cloud.sql，CREATE INDEX IF NOT EXISTS；2 个 recency 索引尾键含 `id DESC`）。
- **确定性全序破除键**（worker：8 条 recency 显示查询 `ORDER BY COALESCE(...) DESC, id DESC`）。
- **query plans + determinism**（`query_plans.json`）：EXPLAIN QUERY PLAN before/after + p95 + 规模 + 跨族并列确定性。
- **工具** `tools/db_query_plan.py`：真 schema 建 pre/post SQLite（**含跨族并列**）比 plan/p95/规模/确定性。
- **pre_fix_schema.sql**、**独立对抗复核** adversarial_review.md（含 hole 发现与修复）。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/query_plan_tests.txt`（ACCEPTANCE = PASS）。

1. **D1 rows scanned 和 p95 下降** — 5/5 热查询 SCAN/临时排序 → 索引 SEARCH（**无临时 B-tree**，p95 降 3–200×）；规模：pre 随 N 增长、post 恒平 → rows scanned O(N)→O(LIMIT)。**负控制**：pre-T083 全表扫。
2. **确定性（关闭 hole）** — 合成数据**含跨族并列**（cross_family_ties_present=True）；破除键查询确定全序（index==forced-scan）、**OFFSET 分页不跳不重**；8 条 recency ORDER BY 全带 `, id DESC`。
3. **无布局跳动回归** — 服务端渲染无 CLS；**六主题合同逐字节不变**（查询在页面体）；recency 单调。**CWV 达标不声称**。

## 实时未回归
NOT_DEPLOYED：改 schema+worker、重算 build_id(d1dfcb3b7447)，不部署。live `/build.json`=b189d3cc0703（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 0（NOT_DEPLOYED）。**部署后**：索引写放大（每次 INSERT/UPDATE cn_items/cn_events/cn_reviews/cn_lessons 多更新对应索引 + 存储；读多写少值得，cron 批量写量小）。破除键使 recency 查询确定，无额外成本。只读 GET 1；人工=索引+破除键+query-plan/determinism 工具+验证器+复核。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
