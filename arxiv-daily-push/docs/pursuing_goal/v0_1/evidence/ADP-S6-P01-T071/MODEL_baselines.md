# MODEL card · ADP-S6-P01-T071｜历史频率与季节性统计基线

> 这是 v0_1 认知系统 S6 回测层的**第一个统计模型**的正式规格（per AGENTS.md 模型纪律）。release_mode=NOT_DEPLOYED；运营级 `docs/governance/MODEL_SPEC.md` / `formula_registry.yaml` 的 ID 注册**门控于认知层向生产的 promotion**——本 MODEL card 是该 NOT_DEPLOYED 模型的 evidence-backed 规格（历史上 v0_1 全部工具均以 in-evidence 方式记录，运营 MODEL_SPEC 只跟踪已部署交付系统）。

## 模型身份
- **model**: ADP-V01-S6-BASELINE（两个便宜可解释基线：frequency、seasonality）
- **tool**: `tools/baselines.py`
- **purpose**: 复杂模型必须**先打败**便宜可解释基线；每个预测目标至少有一个可重跑基线，否则不得开发高级模型。
- **inputs**: 每个目标的历史结算结果 `history = [{observed_at:'YYYY-MM-DD', label:0|1}]`（label 由 T069 结算规则在 T070 防泄漏快照上产生）。
- **outputs**: 每个目标每个基线的概率预测 + metrics（Brier、accuracy@0.5）。

## 公式（formulas）
- **FREQ（frequency baseline）**：`P(event) = (Σ label) / N`，N=历史有效样本数；N=0 时 P=0。**便宜、可解释=基础发生率**。
- **SEAS（seasonality baseline，Laplace 平滑）**：对月份桶 m，`P(event|m) = (events_m + α·glob) / (n_m + α)`，`glob=全局基础发生率`，α=1（Laplace）。**未见过的月份回退到平滑后的全局率**（不硬判 0/1）。
- **Brier**：`(1/N)·Σ (p_i − y_i)²`（概率的均方误差，越低越好；always-0.5→0.25）。
- **accuracy@0.5**：`(1/N)·Σ 1[ (p_i≥0.5?1:0) == y_i ]`。

## 假设（assumptions）
- 历史结算 label 无未来泄漏（由 T070 observed_at 快照保证）。
- 月份季节性以历法月（1-12）为桶；样本稀疏时 Laplace 平滑防过拟合。
- 基线为**每目标独立**拟合（不跨目标共享参数）。

## 参数（parameters）
- `alpha`（Laplace 平滑）= 1.0（默认；可调，>0）。
- 阈值 `threshold`（accuracy）= 0.5。

## 可复现性（reproducibility）
- **确定性**：无网络/时钟/随机；相同 history → 相同 rate/month_rates → 相同 metrics。`benchmark` 两次运行报告逐字节一致。
- **每目标≥1可重跑基线**：`benchmark` 对每个目标产出 frequency + seasonality 两个基线及其 metrics。
- **门**：`may_develop_advanced(target_id, report)` 仅当该目标已有可重跑基线才返回 True——**无基线不得开发高级模型**。

## 评估与验收
- 见 `test-results/baselines_tests.txt`（ACCEPTANCE=PASS）：每目标有 frequency+seasonality 基线、概率∈[0,1]、Brier 计算、可复现；无基线目标 `may_develop_advanced`=False（负控制）。

## 回滚
- `git revert <sha>`（只读模型库，生产未变更）。运营 MODEL_SPEC 未改，无 ID 需回退。
