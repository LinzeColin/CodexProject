# 独立对抗复核 — ADP V0.2 P02 知识库 /library

复核者：独立 general-purpose skeptic（非实施者；实施者不自签）。方法：把 schema_cloud.sql 灌进真实 sqlite3 跑查询、在 Node 里用 mock D1 跑 `libraryPage` 本体，力图证伪。

## 第一轮：BLOCK（抓到真实的免费档违规）

**BLOCK — 两条查询都全表 SCAN `cn_items`。** D1 不带 `ANALYZE`（`schema_cloud.sql` 与 worker 里都没有），规划器无行数统计，于是从**大表**驱动 join、逐行探测 `cn_reviews`：

```
STATS: SCAN i USING COVERING INDEX idx_cn_items_board_recency
       SEARCH r USING INDEX sqlite_autoindex_cn_reviews_1 (item_id=?)
```

实测（`cn_reviews` **固定 500 行**，只变 `cn_items`，证明代价挂在"只被 join 进去"的那张表上）：

| cn_items | STATS | LIST |
|---|---|---|
| 1,000 | 0.4 ms | 0.8 ms |
| 20,000 | 4.0 ms | 4.6 ms |
| 200,000 | 33.1 ms | **39.4 ms** |

即**每次页面访问读约 2×|cn_items| 行**；200k 条时约 40 万行/次。D1 免费档 **5M 行/天**且与每日 cron 及所有页面共享 → **十几次浏览耗尽当天预算**。这直接违反 Owner 于 T087 签署的 **$0/mo 免费档基线（DIR-007）**，并**回归了已上线的 T083**（T083 的交付物正是消除热路径全表扫描；其证据里 `today_recency` 修复前正是被标 `full_scan: true`）。且 `cn_items` 随每日 cron 与 S4 的 2016+ 回填**只增不减**。

其余第一轮全 PASS（均为执行验证而非目测）：schema/列名逐一对真实 schema 核对存在；`i.*` 与 `r.*` 五个别名字段**零重名**，未遮蔽 `factsheetHTML` 所需字段；`?1` 用两次 + `?3` 配 3 个 bind **正确**（SQLite 参数个数取最大索引）；注入（`board="' OR 1=1--"` → 0 行而非全表）与 XSS（`<script>`/`onerror`/`javascript:`/`"><svg onload>` 全部被 `esc` + 双引号属性 + `encodeURIComponent` + `safeHref` 中和）；空值/零行不崩；路由精确匹配不遮蔽 `/item/`、`/board/`；诚实性（页面不提笔记/版本/许可/导出，符合 T067 拒绝规则）。

**修复**：`JOIN` → **`CROSS JOIN`**（SQLite 将左表钉为外层循环，经 `ON` 仍是内连接）。另修掉无法被筛选到的 `—` 分面芯片。

## 第二轮：CONFIRMED_SOUND

- **语义同一**：200k×2k 下 `CROSS JOIN` vs `INNER JOIN` **7 种筛选组合 diff=0**；joined rows = 2000 = `cn_reviews` 行数（真笛卡尔积会是 4 亿）→ **无笛卡尔积**。
- **`cn_items` 永不扫描**：两查询计划均为 `SCAN r` + `SEARCH i USING INDEX sqlite_autoindex_cn_items_1 (id=?)`（由真实的 `cn_items.id TEXT PRIMARY KEY` autoindex 支撑）。200k 下 STATS 49.3→8.3ms、LIST 57.1→2.4ms（6–24x）。**T083 无全表扫描标准恢复**；代价改挂在 `cn_reviews`（用户主动行为有界）而非 `cn_items`（流水线喂养、随回填无界增长）。
- **该修复比声称的更强**：负控制只在**无 ANALYZE 统计**时复现（D1 的常态）；`CROSS JOIN` 在**有无统计时都**钉住正确计划，而不是依赖 D1 不会替你跑的 ANALYZE。
- **TEMP B-TREE 可接受**：只排 `cn_reviews` 行。~2k 复习条目 → ~8k 行/页 → 对 5M/天约 625 次/日；即便病态的 5 万条也约 100ms/页。有界于用户主动行为，轴是对的。
- **`—` 芯片修复正确**：旧芯片**可证死**（`WHERE evidence_state = '—'` 恒 0 行，真实值是 NULL）；删除不丢信息（NULL 态条目仍经"全部"与板块芯片可见，列表仍显示 `—` 徽章）。板块芯片求和==总数；状态芯片求和==总数−NULL 数，UI 未声称分面穷尽，优于一个点进去空页的芯片。
- **无新缺陷**；BUILD 自哈希复算一致，`build_id == sha[:12]`。

## 复核者对我方证据的一处纠正（已采纳）

我最初写"重跑 visual_regression_ci → PASS"。复核者指出 `visual_regression_ci.py` **没有 `__main__`**，裸跑会 exit 0 且零输出——正是 T086 那种"恒真永不判 blocker"的空跑陷阱，故该表述**不可复现**。
复核者改用真实 API 做**差分**检验并确认：**本 diff 未移动任何视觉契约元素**（HEAD vs 工作树，`asset_hashes` 逐元素比对）；`theme_set_consistency` 六主题齐全。
另一发现（**记为待办**）：对**冻结的 T077 manifest** 跑 `run_ci` 会 `BLOCK on ['base_css','keyframes']`，但**在 HEAD 上同样 BLOCK**——是 T079–T084 已批准改动相对陈旧 T077 基线的**既有漂移**，非本次改动；应单独重新冻结 T077 基线，否则该 gate 恒 BLOCK 而失去意义。`/library` 亦是 T077 `route_labels` 矩阵里没有的新路由（`PIXEL_LAYER_ENFORCED=False`，页面走标准 `PAGE()` 壳，继承主题）。

**终判：VERDICT: CONFIRMED_SOUND**
