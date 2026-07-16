# TASK_REPORT · ADP-S4-P03-T050｜分批回填 31 省级行政区 (SHADOW)

## 唯一目标（达成）
按 cohort 分批扩展省级政策/统计/专业主管部门数据。**每批通过后才进入下一批；失败省隔离不阻塞全局。** release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：用 T049 A1 family 分批回填省级；批门 gate、失败省隔离。
2. **允许修改文件**：`tools/province_backfill.py`（新）+ `evidence/ADP-S4-P03-T050/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——回填从 **dev-env** 实抓。六主题/MVP 不变。SHADOW。
4. **基线**：main `69972ba4`（T049 已合入）；用 T049 A1ProvinceConnector + T024 内容寻址 + T026 版本。
5. **验收**：每批通过后才进下批；失败省隔离不阻塞全局。
6. **回滚**：`git revert <sha>`（隔离回填证据，生产未变更）。

## 交付物
- `tools/province_backfill.py` —— 分批编排器（plan_batches/run_province/batch_gate/orchestrate/coverage_report）。
- `evidence/…/{province_cohorts.json, province_backfill_docs.json, coverage_report.json, cost_report.json, health_report.json}`。
- `evidence/…/backfill_run.py` —— dev-env 实抓驱动。
- `evidence/…/test-results/{t050_verify.py, backfill_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/backfill_tests.txt，ACCEPTANCE = PASS，exit 0）
- **每批通过后才进下批**：批 0（art-cms：江苏+山东+广东）gate PASS（provinces_ok=2）→ 批 1（beijing-zhengce：北京）gate PASS（provinces_ok=1）。**completed_batches=2, halted_at=None**。
- **失败省隔离不阻塞全局**：**广东**（gd.gov.cn 真实 TLS/连接被挡）→ isolated_failures 记录、**批 0 仍 PASS**（江苏+山东产文档）→ 进批 1。隔离 ≠ 阻塞。
- **9 真实 A1 文档**：江苏 3 + 山东 3 + 北京 3；全 authority_level=A1 + 内容寻址 canonical_id(`ttl:`) + 月份；**日期正确**（江苏 2026-07-14、山东 2026-07-09/07-01/06-16 跨月、北京 2026-07-14；非 T049 修复的 Maketime 渲染时间戳）；真实文号（苏政办函/鲁科字/京科发/京交停车发/京疾传防…）。
- **幂等**：重跑 orchestrate → 同 9 个 canonical_id、0 新。
- **负控制（真门证明）**：整批 0 失败（空 fetcher → 0 文档）→ **halted_at=0、批 1 不跑**、completed_batches=0——证明批门真阻断进程。
- **A1 赢得非假定**：`run_province` 对每篇调 `connector.verify()`，仅保留 `is_official && A1` 的文档，authority_level 取自身份判定（非硬编码）——经对抗复核指出后加固。见 `adversarial_review.md`（skeptic 判 CONFIRMED_SOUND，承重宣称全真）。
- **实时无回归**：SHADOW，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 9 真实 A1 省级文档 + coverage/cost/health 报告。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A1 Expansion）
- **Value**：**分批、门控、隔离的省级回填执行**——渐进扩省，每批 gate，单省失败不拖全局；省级覆盖的执行载体。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = dev-env 分批回填 + 编排器编写。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：3 省/2 批（广东隔离演示）；max_docs=3 代表批；server-rendered 范围（JS/TLS 省需 headless fetcher）；dev-env 宽松 TLS 仅可达性；全域随更多批+T056 累计。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（SHADOW，无 schema/UI/部署变更）。`data-samples` = province_backfill_docs.json + coverage_report.json。

## 完成声明
```text
Task: ADP-S4-P03-T050
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/province_backfill.py(新) + T050 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: backfill_tests.txt —— 2批门控按序过(江苏/山东→北京)；广东隔离不阻塞;9真实A1文档(内容寻址+正确日期+跨月);幂等;负控制(整批失败→halt,下批不跑)；实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A1 省级分批门控回填(9真实文档,失败省隔离)
Data/Performance/Visual: Data=9真实A1文档+报告；Perf=实时无回归；Visual=六主题保留
Value: 分批门控隔离的省级回填执行载体
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW,dev-env)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（dev-env实抓，生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
