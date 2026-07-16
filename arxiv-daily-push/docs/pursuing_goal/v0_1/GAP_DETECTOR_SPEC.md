# Source-Year-Month Gap Detector Spec · ADP-S4-P01-T043

把**全面性**从「来源数量」变为**可见的时间覆盖与缺口**：每个 enabled source × year-month 单元格
要么有 item **count**，要么有明确的**缺口 reason**——**零个静默未解释空洞**；无法解释的单元 → **alert**。
工具：`tools/gap_detector.py`。**NOT_DEPLOYED**。对应目标「2016+ 全面/权威」。

## 覆盖网格（coverage table）

`build_coverage(items)` → `(source_id, month) → count`。`detect(items, sources, months, backfilled, failed)`
对每个 source × 每个月（2016-01…2026-07 = 127 月，来自 T041 分片）分类，产出网格 + reason 统计 + alerts。

## 缺口原因（穷尽、确定性）

| status | 含义 |
|---|---|
| `covered` | count > 0 |
| `source_not_yet_active` | 该月早于源首次活跃（active_from） |
| `no_publications` | 源活跃且该月已回填但确无条目（已解释的空） |
| `not_backfilled` | 该月在计划窗内但其回填分片未完成（pending） |
| `fetch_failed` | 该月回填分片失败 |
| `UNEXPLAINED` | 以上都不是 → **alert**（目标 0） |

`classify` 穷尽分类，使**每个空单元都被解释**；`infer_source_windows` 从已入库条目推每源活跃窗 [首月,末月]。

## 验收（`test-results/gap_tests.txt`，PASS）

真实 500 覆盖：**20 源 × 127 月 = 2540 单元**：
- **每单元有 count 或解释、0 静默空洞**：`covered 75 / not_backfilled 203 / source_not_yet_active 2262`（和=2540），**unexplained=0**，every_cell_has_count_or_reason=True。
- **alert 有效（不糊弄）**：注入无活跃窗的 `ghost-source` → **127 unexplained → 127 alerts**，证明检测器**会抓静默空洞**而非把一切都解释掉。

## 边界

`backfilled/failed` 月集接真实回填状态（T041/T042）后填充；本任务 backfilled 空集 → 历史空月归 `not_backfilled`（pending，正确：真实回填未跑，NOT_DEPLOYED）。源活跃窗由已入库条目推断（真实源上线日期接线时以注册表 enabled_at 校准）。
