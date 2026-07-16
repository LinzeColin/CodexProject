# Known gaps · ADP-S7-P03-T083｜优化 Bundle、D1 查询、流式布局和长列表

诚实披露**范围**、**成本**、**验证形式**、**复核发现的 hole 及修复**与 NOT_DEPLOYED 语义。

## 实现（含复核后的修复）
- **5 个 D1 索引**（schema_cloud.sql，CREATE INDEX IF NOT EXISTS，幂等+additive）；两个 recency 索引尾键含 `id DESC`。
- **确定性全序破除键**（worker）：8 条 recency 显示查询 `ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC`（选择池用 `, i.id DESC`），与既有淘汰查询（worker line 352）一致。查询由 SCAN+临时排序 → 索引顺序 SEARCH（无临时 B-tree），且相同 recency 的并列项顺序确定。
- **六主题视觉/动效合同逐字节不变**（查询改在 todayPage/radarPage/boardPage/browse 等页面体函数，非合同哈希）；服务端整页渲染 → 无 CLS。BUILD 重算 0cb3acee6bf3→d1dfcb3b7447。

## ★独立复核发现的 hole 及修复（如实记录）★
- **hole**：初版**仅加索引、无破除键**。skeptic 证：在**跨族并列**（一行 recency 源自 published_at、另一源自 fetched_at，两者 COALESCE 相等）时，board/browse 的 `LIMIT/OFFSET` **页成员与顺序 pre 与 post 不同**（联合集不丢/不重，但页边界翻动）；且 `ORDER BY ... DESC LIMIT ? OFFSET ?` **无全序 → OFFSET 分页可跳/可重**。
- **验证器盲点**：初版合成数据把 published_at 放 2016、fetched_at 放 2026（不相交命名空间）→ 跨族并列**不可能构造** → 「结果中性」检查**空过**（vacuous）。
- **修复**：①给全部 recency 显示查询加 `, id DESC` 全序破除键（+ 索引尾键含 id DESC，保持索引完全服务、无临时排序）→ 顺序确定、OFFSET 分页不跳不重；②验证器合成数据现构造**跨族并列**并断言 index==forced-scan（确定性）、页不相交、跨族并列存在（`cross_family_ties_present=True`）——盲点关闭。
- **定性**：这不是「结果回归」，而是把**本就未定义的并列顺序**变确定（更正确）；无 recency 更高的行被丢/错序（单调性已验），六主题合同不变。

## 成本 / 写放大（部署后）
- 索引写放大：每次 INSERT/UPDATE cn_items/cn_events/cn_reviews/cn_lessons 多维护对应索引 + 存储。读多写少值得（读扫描行大降、省 D1 读额度；写只在每日 cron 批量）。破除键无额外成本（索引已服务）。
- **可能冗余**：`idx_cn_items_board_recency` 覆盖旧 `idx_cn_items_board` 多数用途；保守未删。

## 验证形式 / 范围（如实）
- **本地 SQLite EXPLAIN QUERY PLAN + p95 + 确定性**：D1 是 SQLite 内核，plan/确定性跨 SQLite 一致（载重）；**绝对 p95 毫秒**是本地内存 SQLite，真实 D1 网络 p95 须部署后测。**CWV 达标不声称**（无字段数据，T081 规则）。
- **交付物覆盖**：`query plans/indexes` 实做（核心）；`bundle diff` = worker 仅查询串 +少量字节（tie-breaker），六主题合同不变；`virtualization/skeleton` **moot**：服务端整页渲染、增长表列表全 LIMIT 有界分页 → 无未分页长列表。
- **搜索 LIKE 未优化**（前导通配无法索引，需 FTS5）——LIMIT 40 有界，列为后续 FTS 升级。
- **NOT_DEPLOYED**：live 仍 b189d3cc0703；索引部署时建。T077 基线不重冻。
