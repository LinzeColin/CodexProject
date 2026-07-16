# TASK_REPORT · ADP-S6-P02-T072｜实现 2016+ Rolling-origin Backtest

## 唯一目标（达成）
**用真实时间顺序验证泛化和领先时间**：对 2016+ 已结算结果做 **rolling-origin backtest**——对每个滚动起点 O，训练集=观测于 O 之前的历史（T070 防泄漏），拟合 T071 频率/季节性基线，验证集=观测于 (O, O+horizon] 的未来结果，评分（Brier）。**至少三个滚动窗口；训练/验证时间不交叉；结果可重跑**。开启 S6-P02（滚动回测、校准与 Ledger）。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：滚动起点回测（≥3窗口，训练/验证时间不交叉，可重跑）+ split generator + run manifest + results。
2. **允许修改文件**：`tools/rolling_backtest.py`（新）+ `evidence/ADP-S6-P02-T072/*` + 治理同步。**不改 worker/生产/registry/VERSION**。复用 T070 dataset_snapshot + T071 baselines + T056 _parse_date。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、**无时钟**（origins 传入）。**复用 T071 基线模型（其 MODEL card 已存），本任务为回测 harness 非新模型**——运营 MODEL_SPEC 未改。
4. **基线**：main `656b384f`（T071 已合入）；2016-2022 结算时序（三月聚集）+ 3 滚动起点。
5. **验收**：≥3窗口；训练/验证时间不交叉（含边界+泄漏 guard；负控制注入 crossing 样本被抓）；可重跑（结果+manifest 一致，改 horizon 变 manifest）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/rolling_backtest.py` —— `rolling_splits`（split generator：每起点 O → train=观测<=O / val=观测∈(O,O+horizon]，时间不相交）+ `assert_no_time_crossing`（train 观测<=O < val 观测，否则 raise）+ `run_backtest`（每窗口拟合 T071 基线于 train、评分于 val；对每 train 集用 **T070 泄漏 guard**；返回 per-window metrics + run_manifest）+ `run_manifest`（对 target/origins/horizon/windows 的确定性哈希）。
- `evidence/…/build_rolling_backtest.py`（2016-2022 结算时序[三月聚集] + 3 起点[2019/2020/2021] + 1年验证窗）+ `rolling_backtest_report.json` + `test-results/{t072_verify.py, rolling_backtest_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/rolling_backtest_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 至少三个滚动窗口**：3 窗口（起点 2019/2020/2021），每窗口有非空 train/val（train_n 9/12/15，val_n 3/3/3）。
- **② 训练/验证时间不交叉**：每窗口 **train 观测<=origin < val 观测∈(origin, val_end]**，无样本同属 train 与 val；每 train 集经 **T070 泄漏 guard**（无未来观测）。**负控制（判别力）**：注入**起点后观测的 train 样本** 与 **起点前观测的 val 样本** → `assert_no_time_crossing` **均 raise**。
- **③ 结果可重跑**：两次 `run_backtest` **结果+manifest 完全一致**（`bt:06d6397caf6b3ab4`）；**改 horizon(365→180) → manifest 不同**（内容敏感）。
- **时间顺序泛化（真信号）**：起点前移 **train_n 增 9→12→15**；**季节性 Brier 随更多三月历史递减 0.0139→0.0089→0.0062**——真实时间顺序泛化改善，非平凡/非泄漏（训练 2016-2018.. 与验证 2019.. 严格时间不交叉）。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 2016-2022 结算时序（21 样本，三月聚集）+ 3 起点 + 1年验证窗。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S6 预测校准）
- **Value**：**真实时间顺序的诚实回测**——滚动起点验证泛化与领先时间；训练只见起点前的历史（T070 防泄漏）、验证只在未来窗口、二者时间不交叉；结果可重跑带 manifest（可审计）。为 T073+ 校准/Ledger 与"复杂模型必须打败基线"提供无泄漏、时间正确的回测框架。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；**模型调用 0（本地确定性统计，无 LLM）**；人工维护 = 回测 harness + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：回测 harness 复用 T071 基线模型（其 MODEL card 已存，本任务非新模型故运营 MODEL_SPEC 未改）；rolling 为 expanding-origin（可扩展为固定窗/多目标）；真实 D1 run manifests 物化由部署阶段负责。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = rolling_backtest_report.json。`benchmarks` = rolling_backtest_report.json（per-window Brier）。

## 完成声明
```text
Task: ADP-S6-P02-T072
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/rolling_backtest.py(新) + T072 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动；复用T071基线模型运营MODEL_SPEC未改
Tests: rolling_backtest_tests.txt —— 3滚动窗口;每窗口train观测<=origin<val观测无交叉+T070泄漏guard;crossing负控制(起点后train/起点前val)均raise;两次结果+manifest一致改horizon变manifest;时间顺序train_n增9→12→15季节性Brier改善0.0139→0.0062;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 2016+ Rolling-origin Backtest(split generator+run manifest+results,≥3窗口,时间不交叉,可重跑)
Data/Performance/Visual: Data=2016-2022时序+3起点；Perf=实时无回归；Visual=六主题保留
Value: 真实时间顺序诚实回测,训练只见起点前历史防泄漏,验证在未来窗口,可重跑带manifest
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性统计无LLM)；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
