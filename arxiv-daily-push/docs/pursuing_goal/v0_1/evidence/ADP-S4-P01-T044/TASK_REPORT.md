# TASK_REPORT · ADP-S4-P01-T044｜建立 Source-Year 单位成本与维护看板

## 唯一目标（达成）
在**扩每个 cohort 前**知道**抓取、存储、AI、失败和人工维护**成本。交付 cost facts、throughput、failure/manual intervention metrics。**未知成本不得用 0；可计算每千 artifact 和每个 accepted material event 成本。**

## 六个开始前问题（已回答）
1. **唯一目标**：Source-Year 成本看板；未知成本标 UNKNOWN 不用 0、可算每千 artifact/每 accepted event 成本。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/cost_dashboard.py, COST_DASHBOARD_SPEC.md}` + 本证据包（cost_items/cost_dashboard_report/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接生产。NOT_DEPLOYED。
4. **基线**：main `a0f032ba`（T043 gap detector 已合入）；throughput 用真实 500 抓样。
5. **验收**：未知成本不得用 0；可计算每千 artifact 和每个 accepted material event 成本。
6. **回滚**：`git revert <sha>`（纯看板，生产未变更）。

## 交付物
- `tools/cost_dashboard.py` —— `build_facts`（每 source-year：throughput[artifacts/accepted_events] + cost fields[fetch_subrequests/storage_bytes/model_calls] + ops[failures/manual_interventions]，**未测=UNKNOWN 绝不 0**）+ `unit_costs`（**逐资源** cost_per_1000_artifacts / cost_per_accepted_event，UNKNOWN 传播）+ `dashboard`。
- `COST_DASHBOARD_SPEC.md` + `evidence/.../{cost_items.json, cost_dashboard_report.json}`。

## 验收结果（实测，见 test-results/cost_tests.txt，ACCEPTANCE = PASS，exit 0）
真实 500 throughput + 2 个 source-year 测得成本：**30 source-years（2 computable / 28 unknown-cost，unknown 成本格 84 / 真 0 格 2）**：
- **未知成本不得用 0**：未测 source-year 成本全 **UNKNOWN**（派生单位成本 UNKNOWN），**无未测成本被显示为 0**（`no_unknown_cost_shown_as_zero=True`）；测得的**真 0**（model_calls=0）作为已知 0 保留，**与 UNKNOWN 区分**。
- **可计算每千/每 accepted**：`arxiv-all|2025`（22 artifacts/8 accepted）**per-1000 fetch 5454.5 / per_accepted fetch 15.0**（数值校验通过）；`nejm|2026`（20/7）per-1000 fetch 1500 / per_accepted 4.29。
- **throughput + failure/manual 指标齐备**。

## Data / Performance / Visual
Data = 30 source-year 成本看板（2 computable + 28 UNKNOWN）。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S4 2016+ Expansion）
- **Value**：扩 cohort 前**看清真实成本**——每 source-year 的抓取/存储/AI/失败/人工维护成本，**未知即 UNKNOWN 绝不用假 0**，可算每千 artifact / 每 accepted event 单位成本；扩张决策基于真成本而非虚 0。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 看板（真实用量校准）。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接生产；measured 接真实用量后填充）；多数成本 UNKNOWN（有意，落实未知≠0）；成本单位为资源非货币（免费档）；accepted_events 演示标记（接 cn_selections）；人工维护/失败为 ops field；看板 UI 未做。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke` —— N/A。`data-samples` = cost_items.json + cost_dashboard_report.json。

## 完成声明
```text
Task: ADP-S4-P01-T044
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/cost_dashboard.py + COST_DASHBOARD_SPEC.md + T044 证据包（cost_items/cost_dashboard_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: cost_tests.txt —— 30 source-years(2 computable/28 unknown)；未知成本全UNKNOWN不0(真0 model_calls保留)；per-1000/per-accepted可算(arxiv-all|2025 fetch5454.5/1000,15.0/accepted;nejm|2026 1500,4.29)；throughput+failure+manual齐备，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Source-Year成本维护看板(未知成本≠0，可算每千artifact/每accepted成本)
Data/Performance/Visual: Data=30 source-year成本看板；无性能/UI
Value: 扩cohort前看清真成本，未知UNKNOWN不用假0
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（看板逻辑，未接生产）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
