# TASK_REPORT · ADP-S4-P04-T054｜按边际价值扩展 A2 Registry (SHADOW)

## 唯一目标（达成）
只扩展能提供项目/试点/招采/产业落地第一线信号的 A2。交付 A2 cohorts、marginal value report、health。**新增 cohort 的 verified useful signal rate 不低于既有 A2 基线。** release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：按边际价值扩展 A2；新增 cohort useful-signal rate ≥ 既有 A2 基线。
2. **允许修改文件**：`tools/a2_registry.py`（新）+ `evidence/ADP-S4-P04-T054/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——本任务=选择/评估，无抓取执行。六主题/MVP 不变。SHADOW。
4. **基线**：main `4790d246`（T053 已合入）；读 T053 pilot manifest 作 A2 基线；复用 T053 a2_pilot 模型。
5. **验收**：新增 cohort 的 verified useful signal rate 不低于既有 A2 基线。
6. **回滚**：`git revert <sha>`（选择产物，生产未变更）。

## 交付物
- `tools/a2_registry.py` —— baseline_from_t053 + evaluate(边际第一线信号+官方) + useful_signal_rate + expand。
- `evidence/…/a2_expansion.json` —— 8 新增 cohort + 2 拒绝 + marginal value report + health + 基线对比。
- `evidence/…/build_expansion.py`、`evidence/…/test-results/{t054_verify.py, expansion_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/expansion_tests.txt，ACCEPTANCE = PASS，exit 0）
- **新增 cohort rate ≥ 既有 A2 基线**：既有基线（T053）=1.0（10 区全 official+≥1 增量信号）；**新增 8 区 rate=1.0 ≥ 1.0**，meets_baseline=True。
- **只加第一线信号 A2**：8 新区（南沙/舟山/西海岸/合肥高新/东湖高新/滨海/江北/成都高新）全 verified-useful（official + ≥1 第一线信号[项目/招采/试点/产业落地/招商/规划]），边际价值排序。
- **无价值源不加（负控制）**：**baseline-only-zone（仅 policy/regulation/statistics，0 第一线）拒**；**zone-aggregator（media，非官方）拒**。**负控制证明门真过滤**：若纳入这 2 个，rate 降到 **0.8 < 基线 1.0**。
- **交付物齐**：A2 cohorts（8 admitted）+ marginal_value_report（逐候选）+ health（每 admitted 区）。每区 2016 游标。
- **实时无回归**：SHADOW，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 8 新增 A2 区 + marginal report + health + 2 拒绝。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A2 Expansion）
- **Value**：**价值保持的 A2 扩展**——只加真带第一线信号的区，新增 cohort useful-signal rate 不降；扩数量不摊薄质量。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 边际价值模型 + 扩展区候选。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：基线读自 T053；rate 是 TYPE 层(单条真实 useful 率随抓取+T055 30日健康)；选择非抓取；8 新区 tls_blocked pending；SHADOW 未部署，生产门是 T055。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（SHADOW）。`data-samples` = a2_expansion.json。

## 完成声明
```text
Task: ADP-S4-P04-T054
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/a2_registry.py(新) + T054 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: expansion_tests.txt —— 新增8区cohort rate 1.0≥既有A2基线1.0；只加第一线信号A2(南沙等8)；无价值源不加(baseline-only拒/media拒);负控制(纳入被拒者rate降0.8<基线)证明门真过滤;deliverables齐(cohorts+marginal report+health);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A2 registry边际价值扩展(8新区,rate不降,价值保持)
Data/Performance/Visual: Data=8新A2区+report+health；Perf=实时无回归；Visual=六主题保留
Value: 价值保持的A2扩展,扩数量不摊薄质量
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（cohorts+report+health；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
