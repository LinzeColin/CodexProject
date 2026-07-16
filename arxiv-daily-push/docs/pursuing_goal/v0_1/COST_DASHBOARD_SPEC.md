# Source-Year Cost + Maintenance Dashboard Spec · ADP-S4-P01-T044

在**扩每个 cohort 前**知道每个 source-year 的**抓取 / 存储 / AI / 失败 / 人工维护**成本。
硬规则（DIR 口径）：**未知成本不得用 0**——未测得的成本是字面 `"UNKNOWN"`，依赖它的派生单位成本也是 `"UNKNOWN"`。
工具：`tools/cost_dashboard.py`。**NOT_DEPLOYED**。

## Cost facts（每 source-year）

`build_facts(items, measured)` → 每 (source_id, year)：
- **throughput**：`artifacts`（条目数）、`accepted_events`（accepted material event 数）——从 items 计数。
- **cost fields**：`fetch_subrequests`（Worker 子请求）、`storage_bytes`（R2 字节）、`model_calls`（AI 调用）——来自 `measured`，**未测=UNKNOWN，绝不 0**。
- **ops fields**：`failures`、`manual_interventions`——同上，未测=UNKNOWN。

成本用**资源单位**计（免费档 DIR-007，经常性 ≈$0；资源才是真约束）。

## 单位成本（每千 artifact / 每 accepted event）

`unit_costs(fact)`：**逐资源**给 `cost_per_1000_artifacts` 与 `cost_per_accepted_event`（子请求/字节/模型调用不混加）。
任一资源 UNKNOWN 或缺分母 → 该资源单位成本 `UNKNOWN`（不 0）。`recurring_usd_month=0`（免费档）。

## Dashboard

`dashboard(items, measured)`：每行 = fact + 单位成本 + `cost_computable`（全部成本已测才 True）。
汇总 `computable_rows / rows_with_unknown_cost / unknown_cost_cells / zero_cost_cells`，`no_unknown_cost_shown_as_zero=True`（构造保证）。

## 验收（`test-results/cost_tests.txt`，PASS）

真实 500 throughput + 2 个 source-year 测得成本：**30 source-years（2 computable / 28 unknown-cost）**：
- **未知成本不得用 0**：未测 source-year 成本全 `UNKNOWN`（派生单位成本 UNKNOWN），**无未测成本被显示为 0**；测得的**真 0**（model_calls=0）作为已知 0 保留，与 UNKNOWN 区分。
- **可计算每千/每 accepted**：`arxiv-all|2025` per-1000 fetch 5454.5、per_accepted fetch 15.0；`nejm|2026` per-1000 fetch 1500、per_accepted 4.29（数值校验通过）。
- throughput + failure/manual 指标齐备。

## 边界

`measured` 成本接真实用量（Worker 分析/R2 用量键 r2_YYYYMM_*/模型计数）后填充；本任务演示 2 个测得 source-year + 其余 UNKNOWN 的诚实口径。人工维护量为 ops field（接真实工单/失败日志）。未接生产看板 UI（属后续）。
