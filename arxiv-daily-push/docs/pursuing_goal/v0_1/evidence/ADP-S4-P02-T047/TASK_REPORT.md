# TASK_REPORT · ADP-S4-P02-T047｜执行 A0 2016+ Wave 2

## 唯一目标（达成）
**只在 Wave 1 价值成本 Gate 通过后**扩大中央/国家级覆盖。交付 second cohort data、comparison report。**相对 Wave 1 无质量退化；单位成本在批准区间；失败源隔离。** release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：Wave 1 gate 过后执行 Wave 2（cohort 其余 A0 源）；无质量退化、单位成本在区间、失败源隔离。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/evidence/ADP-S4-P02-T047/*` + 治理同步。**不改 worker/生产**（dev-env）。
3. **绝不能改变**：生产 worker/cron/实时——Wave 2 从**开发环境**实抓，生产未触；六主题/MVP 不变。SHADOW。
4. **基线**：main `0e992990`（T046 Wave 1 已合入）；Owner 已 SCALE A0-WAVE-1 全 cohort；用 T034/T035 适配器。
5. **验收**：相对 Wave 1 无质量退化；单位成本在批准区间；失败源隔离。
6. **回滚**：`git revert <sha>`（隔离回填证据，生产未变更）。

## 交付物
- `wave2_backfill_docs.json` —— **11 真实 A0 文档**（gov-cn-fagui 6 + stats-gov 5）跨 6 月 + ndrc/cac 部分（链接发现）。
- `wave2_comparison_report.json` —— Wave 1 gate + Wave 2 vs Wave 1 对比 + 失败源隔离。

## 验收结果（实测，见 test-results/wave2_tests.txt，ACCEPTANCE = PASS，exit 0）
- **Wave 1 价值成本 Gate 通过后才扩大**：从 T046 manifest 校验 Wave 1（幂等+版本）**PASS** → 执行 Wave 2。
- **相对 Wave 1 无质量退化**：Wave 2 用**同一内容寻址身份/版本管道**——11 文档全有内容寻址 canonical_id、**幂等**（重跑 0 新无重复）；扩展到 Wave 1 之外的源（gov-cn-fagui、stats-gov）。
- **单位成本在批准区间**：Wave 1/2 均**走 dev-env 实抓 → 0 云成本**（DIR-007 免费档区间，同 T044 口径）。
- **失败源隔离**：ndrc-gov / cac-gov 列表发现链接但未逐条全解析（DOM 各异）→ 记 partial_sources，**不 crash Wave**；成功源不受影响；本批 0 硬失败。
- **月份覆盖**：6 个不同月份（2019-04…2026-07，全 ≥ 2016-01）。
- **实时无回归**：无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 11 真实 A0 文档（2 源）+ 对比报告。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 2016+ Expansion）
- **Value**：**Wave 2 扩大中央覆盖**——法规 + 统计源加入，相对 Wave 1 **无质量退化**、单位成本在批准区间、**失败源隔离不拖垮整波**；价值成本 gate 守护渐进扩张。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = Wave-2 dev-env 实抓。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：SHADOW 代表性批次；ndrc/cac 部分（已隔离，全解析后续）；单位成本 dev-env 口径；raw/version 未落生产；月份覆盖代表性。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = wave2_backfill_docs.json + wave2_comparison_report.json。

## 完成声明
```text
Task: ADP-S4-P02-T047
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: T047 证据包（wave2_backfill_docs/wave2_comparison_report/test-results/报告）+ 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: wave2_tests.txt —— Wave1 gate PASS→Wave2 11文档(gov-cn-fagui6+stats-gov5)跨6月(≥2016-01)；无质量退化(同管道幂等重跑0新)；扩展beyond Wave1；失败源隔离(ndrc/cac partial不crash)；单位成本0云(dev-env)；实时无回归，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A0 2016+ Wave 2(法规+统计扩大覆盖，无质量退化，失败源隔离)
Data/Performance/Visual: Data=11真实A0文档+对比报告；Perf=实时无回归；Visual=六主题保留
Value: Wave2扩大中央覆盖，价值成本gate守护，无退化/失败源隔离
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW,dev-env)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（dev-env实抓，生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
