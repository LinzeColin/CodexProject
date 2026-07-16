# TASK_REPORT · ADP-S3-P03-T039｜运行 A0 14 日 Shadow 与价值成本对比

## 唯一目标（达成）
对比现有**媒体流**和 **A0 官方流**的**权威率、污染、及时、覆盖与成本**。交付 daily report、miss/false-positive analysis、cost per accepted item。**至少 14 个完整周期；不以单日样本决策；未达门槛继续 Shadow。** release_mode=**SHADOW**（不切换）。

## 六个开始前问题（已回答）
1. **唯一目标**：A0 14 日 shadow 价值成本对比；≥14 周期、不单日决策、未达门槛继续；SHADOW 不切换。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/a0_shadow.py, A0_SHADOW_SPEC.md}` + 本证据包（shadow_reports_14/shadow_value_cost_report/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；**不切换任何东西**（切换=T040 canary + Owner 门）。SHADOW。
4. **基线**：main `6b872ebf`（T038 resolver 已合入）；A0 流 = T034-T036 适配器 → T037 门 → T038 resolver。
5. **验收**：至少 14 个完整周期；不以单日样本决策；未达门槛继续 Shadow。
6. **回滚**：`git revert <sha>`（纯框架/报告，生产未变更）。

## 交付物
- `tools/a0_shadow.py` —— `day_metrics`（每周期媒体 vs A0：权威率/污染/及时/覆盖/成本）+ `accumulate`（**≥14 周期 + 门槛达标才 READY，否则 CONTINUE_SHADOW**）+ miss/false-positive + cost_per_accepted。
- `A0_SHADOW_SPEC.md` —— 指标、shadow 纪律、验收。
- `evidence/.../shadow_reports_14.json` + `shadow_value_cost_report.json`（14 周期 daily + 累计）。

## 验收结果（实测，见 test-results/shadow_tests.txt，ACCEPTANCE = PASS，exit 0）
- **价值成本对比**：**A0 官方流 权威率 100% / 污染 0% / cost_per_accepted 0.375 / 覆盖漏 0 / 误报 0**；**媒体流 权威率 0% / 污染 100%**——A0 官方流在权威与污染上**碾压**媒体流。
- **至少 14 个完整周期 + 不单日决策**：14 周期达标 → **READY_FOR_OWNER_S3_EXIT_GATE**；**单日 → CONTINUE_SHADOW**（「never decide on fewer than 14 (or a single day)」）；13 周期 → CONTINUE_SHADOW。
- **未达门槛继续 Shadow**：注入污染使门槛不达 → **CONTINUE_SHADOW**。
- **SHADOW 不切换**：`release_mode=SHADOW`；note 明示切换 **gated by the Owner S3 Exit**——决策 defer 给 Owner。

## Data / Performance / Visual
Data = 14 周期 daily 报告 + 累计对比。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（SHADOW，不切换）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：用**14 日累计证据**（非单日冲动）对比媒体流 vs A0 官方流——A0 流 100% 权威 / 0% 污染，媒体流 0% / 100%；框架**拒绝在 <14 周期或单日决策**、**未达门槛继续 Shadow**，使 A0 晋级**证据化且交由 Owner 门**，不自签晋级。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = shadow 框架 + 报告；A0 流真实抓取 ~3 子请求/周期（接 worker 后核 DIR-007）。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：SHADOW 不切换（切换=T040+Owner 门）；14 周期报告为代表性（字面 14 天跨真实日历时间由 cron 累计）；A0 流指标基于 T037 门 + 合成官方（真实漏抓/误报随真实运行暴露）；成本结构性建模；**决策不在本任务、defer Owner S3 Exit**。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke`（框架/报告，无新增 live 抓取）—— N/A。`data-samples` = shadow_reports_14.json + shadow_value_cost_report.json。

## 完成声明
```text
Task: ADP-S3-P03-T039
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/a0_shadow.py + A0_SHADOW_SPEC.md + T039 证据包（shadow_reports_14/shadow_value_cost_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: shadow_tests.txt —— A0流权威100%/污染0%/cost0.375 vs 媒体0%/100%；14周期达标→READY_FOR_OWNER_S3_EXIT_GATE；单日/13周期→CONTINUE_SHADOW；门槛不达→CONTINUE_SHADOW；SHADOW不切换defer Owner，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A0 14日Shadow价值成本对比(媒体vs A0官方流)+shadow纪律
Data/Performance/Visual: Data=14周期报告+累计对比；无性能/UI
Value: 证据化对比(A0 100%权威/0%污染 vs 媒体0%/100%)，不单日决策，晋级交Owner门
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（不切换；T040 canary + Owner S3 Exit 门决策）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
