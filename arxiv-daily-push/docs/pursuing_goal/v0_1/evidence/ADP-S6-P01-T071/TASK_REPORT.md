# TASK_REPORT · ADP-S6-P01-T071｜建立历史频率、季节性和简单统计基线

## 唯一目标（达成）
**复杂模型必须先打败便宜可解释基线**：为每个预测目标从其历史结算结果拟合 **frequency（基础发生率）** 与 **seasonality（月份季节性，Laplace 平滑）** 两个便宜可解释基线 + metrics（Brier/accuracy）+ benchmark 报告。**每个目标至少有一个可重跑基线；无基线不得开发高级模型**。**这是 v0_1 认知系统 S6 回测层的第一个统计模型**，正式规格见 `MODEL_baselines.md`。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：频率/季节性统计基线 + metrics + benchmark；每目标≥1可重跑基线；无基线不得开发高级模型。
2. **允许修改文件**：`tools/baselines.py`（新）+ `evidence/ADP-S6-P01-T071/*`（含 **MODEL card**）+ 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。**运营 MODEL_SPEC/formula_registry 不动**（v0_1 惯例：NOT_DEPLOYED 模型在 evidence 记录 MODEL card；运营注册门控于 promotion）。库层只读、无时钟/随机。
4. **基线**：main `3228e008`（T070 已合入）；2 目标含历史（G1 三月季节性/G2 低发生率）+ 1 无历史目标 G0。
5. **验收**：每目标≥1可重跑基线（含历史目标 frequency+seasonality 可重跑、概率∈[0,1]、Brier）；无基线不得开发高级模型（无历史 G0 无可重跑基线→门拒；负控制）。
6. **回滚**：`git revert <sha>`（只读模型库，生产未变更）。
7. **模型路由（T2/T3）**：本任务为 v0_1 认知系统 S6 回测层的**首个统计模型**。正式模型规格（公式/假设/参数/可复现）记于 `evidence/…/MODEL_baselines.md`；运营 `MODEL_SPEC.md`/`formula_registry.yaml` **未改**（该 122 模型注册跟踪已部署交付系统，本模型 NOT_DEPLOYED，运营注册门控于认知层 promotion）——与 v0_1 全部工具的 in-evidence 惯例一致。

## 交付物
- `tools/baselines.py` —— `frequency_baseline`（基础发生率 P=Σlabel/N）+ `seasonality_baseline`（月份率 Laplace 平滑，未见月回退平滑全局）+ `brier_score`/`accuracy`/`evaluate` + `benchmark`（每目标拟合两基线并评分；**仅历史≥min_history 才 has_reproducible_baseline**）+ `may_develop_advanced`（仅有可重跑基线才允许开发高级模型）。
- `evidence/…/MODEL_baselines.md`（**正式 MODEL card**：身份/公式/假设/参数/可复现/回滚）+ `build_baselines.py`（G1 三月季节性 / G2 低率 / G0 无历史）+ `baselines_report.json` + `test-results/{t071_verify.py, baselines_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/baselines_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 每个目标至少有一个可重跑基线**：含历史目标 G1/G2 各有 **frequency+seasonality** 两基线 + metrics（Brier∈[0,1]）；`benchmark` **两次运行报告逐字节一致（可重跑）**。**正确性**：frequency == 实际基础发生率（G1 0.375=3/8）；所有概率∈[0,1]（含未见月/malformed）；未见月回退**平滑全局率 0.375**（非硬 0/1）。**有意义（非平凡）**：季节性目标 G1 上 **seasonality Brier 0.083 < frequency 0.266——便宜基线捕获真实信号**。
- **② 无基线不得开发高级模型**：G1（有基线）`may_develop_advanced`=True；**G0（无历史）`has_reproducible_baseline`=False、`may_develop_advanced`=False**（无基线不得开发高级模型，**in-benchmark 负控制**）；G9（缺席）/未知/空 baselines 均拒。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 2 含历史目标（G1 季节/G2 低率）+ 1 无历史 G0 + eval 集。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S6 预测校准）
- **Value**：**诚实的模型门**——每个可结算目标先有便宜可解释基线（频率/季节性）与可复现 metrics（Brier），复杂模型必须先打败它；无基线的目标（无历史）明确不得开发高级模型。为 T072（Rolling-origin Backtest）提供"必须打败"的基准与门。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；**模型调用 0（本地确定性统计，无 LLM/外部推理）**；人工维护 = 基线模型 + MODEL card + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：基线为频率/季节性两类（可扩展 persistence/趋势）；季节性桶=历法月（可扩展周/季度）；min_history=1（无历史无可重跑基线）；运营 MODEL_SPEC 注册门控于 promotion（MODEL card 为 NOT_DEPLOYED 正式规格）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = baselines_report.json。`benchmarks` = baselines_report.json（Brier/accuracy）。

## 完成声明
```text
Task: ADP-S6-P01-T071
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/baselines.py(新) + T071 证据包(含MODEL card) + 治理同步（见 changed_files.txt）；无 worker/生产改动；运营MODEL_SPEC未改(NOT_DEPLOYED,MODEL card为in-evidence正式规格)
Tests: baselines_tests.txt —— 含历史目标G1/G2各freq+seas可重跑Brier∈[0,1];benchmark两次一致;frequency==base rate;概率∈[0,1]未见月回退平滑全局;季节性Brier打败频率(捕获信号);无历史G0无可重跑基线门拒(负控制);G9/未知/空baselines拒;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 历史频率+季节性统计基线 + Brier/accuracy metrics + benchmark报告 + 无基线不得开发高级模型门
Data/Performance/Visual: Data=2含历史目标+1无历史+eval；Perf=实时无回归；Visual=六主题保留
Value: 诚实模型门,复杂模型先打败便宜可解释基线,无基线目标不得开发高级模型
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性统计无LLM)；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Model: v0_1认知系统S6回测层首个统计模型;正式规格见MODEL_baselines.md;运营MODEL_SPEC注册门控于promotion(NOT_DEPLOYED)
Deployment: NOT_DEPLOYED（只读模型库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
