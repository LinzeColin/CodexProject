# 独立对抗复核 · ADP-S7-P03-T083｜优化 Bundle、D1 查询、流式布局和长列表

实现者**不自签 PASS**。由独立 skeptic Agent（`general-purpose`）对抗复核，**两轮**：第一轮发现真 hole 并驳回，实现者修复后第二轮复核。

## 第一轮：HOLE_FOUND（真 hole，已修）
- **hole**：初版**仅加索引、无全序破除键**。skeptic 用真实 board/browse 查询（`worker_cloud.js:1070`）证：在**跨族并列**（一行 recency 源自 published_at、另一源自 fetched_at，两者 COALESCE 相等）时，`LIMIT 25` 首页**成员+顺序 pre 与 post 不同**（联合集保留、页边界翻动）；`ORDER BY ... DESC LIMIT ? OFFSET ?` **无全序 → OFFSET 分页可跳/可重**。故「结果中性」主张对并列**为假**。
- **验证器盲点**：初版 db_query_plan 合成数据把 published_at 放 2016、fetched_at 放 2026（**不相交命名空间**）→ 跨族并列**不可能构造** → 「结果相同」检查**空过**（vacuous）。
- **严重度 LOW**：不破形式验收（D1 perf 真降；行重排非 CLS；联合集不丢/不重）；但主张过度 + 验证器盲。

## 修复
1. **全序破除键**：给 8 条 recency 显示查询加 `, id DESC`（选择查询 `, i.id DESC`），与既有淘汰查询（line 352）一致 → 确定全序、OFFSET 分页不跳不重。
2. **索引尾键含 id DESC**（两个 recency 索引）→ 全序查询**仍完全索引服务、无临时 B-tree**（p95 win 保留）。
3. **验证器修盲点 + 加载重证明**：合成数据现构造**真实跨族并列**（66,680 对）；`determinism()` 用 **`NOT INDEXED` 强制真全表扫**作独立 oracle（非被 SQLite 拍平回同索引的子查询）；新增 `tie_breaker_load_bearing()`：**无破除键时 board 查询在 pre-schema(idx_cn_items_board+临时排序) vs post-schema(idx_cn_items_board_recency) 结果不同**（`no_tiebreaker_schema_dependent=True`），**有破除键时跨 schema 相同**（`tiebreaker_schema_independent=True`）——证破除键既**必要**又**充分**。

## 第二轮：CONFIRMED_SOUND（复核原文）
逐向量：
- **(a) 完整** — 全部 8 个 recency ORDER BY 都带破除键（负向前瞻 grep 找到 0 个遗漏：352 淘汰/389 选择/915 today/916 board/1069 browse-all/1070 browse-board/1087 search/1236 board3-a0）；唯二 OFFSET 查询(1069/1070)已修；其余列表安全（cn_selections 按 as_of_date=PK 全序；cn_lessons/reviews/events 是 top-N LIMIT 无 OFFSET）。
- **(b) 仍索引服务** — 真查询 EXPLAIN：browse-all/today/search→`USING INDEX idx_cn_items_recency`；board→`idx_cn_items_board_recency`；**无临时 B-tree**；DESC/DESC 匹配、id 是 TEXT PK 索引/查询一致；p95 保留（3–200× 降、post 恒平 vs pre O(N)）。
- **(c) 真确定** — 自建跨族并列，对**真全扫 oracle（NOT INDEXED→强制临时排序）**逐页相同、OFFSET 页不相交、8 次重排稳定；去破除键→ index≠真序（破除键载重）。
- **(d) 未破坏** — node --check 过；BUILD 自哈希重现 `d1dfcb3b7447`；选择查询 `, i.id DESC` 只在已按 recency 排序内破并列（LIMIT 1200≫日窗候选、评分与顺序无关）；board3-a0/search 正确且索引服务。
- **(e) 验证器诚实** — 合成数据真含跨族并列（非不相交命名空间把戏）；`tie_breaker_load_bearing()` 是**真独立 oracle**（复现 5×），验证器**断言** no_tiebreaker_schema_dependent 与 tiebreaker_schema_independent（不能空过）；源正则 `missing_tb` 读真 worker、去任一破除键即失败（已验反例）。
- **(f) 合同/NOT_DEPLOYED** — `detect_regression(origin/main, new)` 无 specific 合同元素变（仅 aggregate roll-up）；查询改在页面体；BUILD `d1dfcb3b7447`；live 仍 `b189d3cc0703`；CWV 达标正确不声称（T081）；pre_fix_schema 与 origin/main 逐字节同。

## 底线
第一轮确认的 hole（跨族并列产品级非确定 + 盲验证器）已**关闭**：代码在每个 recency 站点有**完全索引服务的全序**；验证器经**三条独立机制**载重证明。**未引入新 hole**。

**VERDICT: CONFIRMED_SOUND**（第二轮复核原文），实现者据此提交。
