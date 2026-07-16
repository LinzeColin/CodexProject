# TASK_REPORT · ADP-S6-P03-T076｜完整 Horizon Shadow + go/stop 决策

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S6-P03-T076（S6 Prediction & Backtest / S6-P03 窄目标预测 Shadow，size S）
- **release_mode**: SHADOW（dev/shadow env；生产未触；实时 build `b189d3cc0703` == T040 不变；0 云成本；**GO 是建议非动作**）
- **Depends**: ADP-S6-P03-T074（来源静默）+ ADP-S6-P03-T075（主题加速/扩散）；复用 T073 forecast_ledger（brier_skill_score/calibration）、T072 rolling backtest

## 6 个前置问题
1. **收尾聚合谁？** — S6-P03 的两个 shadow 预测器：T074 来源静默 + T075 两 pilot（ACCEL/DIFFUSION）。技能维度=T075 的 6 个滚动窗口（有 Brier-per-window）；领先价值维度含 T074 早捕获。
2. **「持续有技能」怎样才算？** — 严格读法：`聚合BSS>0 且 每窗BSS>0`（一个窗口回退即 STOP，不许走运窗口掩盖）。
3. **校准怎么判？** — 主度量 **ECE（count-weighted）≤ tol(0.15)**；max-per-bin 作 diagnostic 报告（稀疏桶噪声，不门控）。
4. **领先价值怎么判？** — `lead_days>0 且 net_human_value(正确−误报)>0`；数字来自 shadow 真实统计。
5. **GO 意味着上线吗？** — **否**。GO 是建议对象，实际展示受 S6 Exit Owner Gate 门控；本任务不触生产（SHADOW）。`disable_flag` 是 rollback 开关。
6. **怎么证明门不是橡皮图章？** — 4 个退化 shadow 各翻转恰一个准则→STOP + 对应 failed_criteria + disable_flag；真实 shadow→GO。门在两个方向都可判别。

## 交付物
- **工具** `tools/horizon_shadow_closeout.py`：`skill_assessment`（每窗 BSS+聚合，sustained=min>0）/ `calibration_assessment`（ECE 主门控 + max-bin diagnostic，reuse T073 calibration）/ `lead_value_assessment`（lead>0 且 净人价值>0）/ `release_decision`（GO iff 三准则全过，否则 STOP+disable_flag+failed_criteria）/ `closeout`（一次性收尾）。
- **shadow closeout + release decision + rollback/disable flag** = `horizon_shadow_closeout_report.json`。
- **known_gaps.md**：GO 是建议非动作、ECE vs max-bin 度量选择如实、构造 fixture、边界。
- **独立对抗复核** `adversarial_review.md`。

## 验收（PASS，verifier 独立重算 BSS 与 ECE）
证据：`test-results/horizon_shadow_closeout_tests.txt`（ACCEPTANCE = PASS，exit 0），verifier `test-results/t076_verify.py`。

1. **Brier skill 为正且稳定** — verifier **自带 BSS 公式重算**：6 窗口 per-window BSS [0.35,0.307,0.357,0.392,0.445,0.467] 全 >0（sustained），aggregate 0.387>0，与工具一致。
2. **校准可接受** — verifier **自带 ECE 公式重算** 0.0925 == 工具 0.0925 ≤ tol 0.15；max-bin 0.333 作 diagnostic 披露。
3. **用户领先价值明确** — lead 90d、净人价值 14（正确 19 − 误报 5）>0、clear True。
4. **go/stop 诚实（load-bearing 门）** — 真实 shadow → **GO**（show True，disable False）；**4 个负控制**各翻转恰一准则→**STOP**：①技能回退窗口→STOP(skill)②失校准(pred0.9 obs0.3,ECE0.6)→STOP(calibration)③无净价值→STOP(lead)④零 lead→STOP(lead)；均 disable_flag True + 精确 failed_criteria。**可复现**：closeout 两次一致。

## 实时未回归 & GO 语义
`/build.json` 实测 `build_id=b189d3cc0703`（== T040）。SHADOW 库层决策任务，无 worker/D1/R2/cron 改动。**GO 是建议**，实际展示仍需 Owner 在 S6 Exit 批准；本任务本身不 surface 给用户、不部署。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 行读 0 / 写 0；R2 字节 0 / 操作 0；model_calls 0；recurring cloud 0（SHADOW，GO 是建议非动作）；人工维护=决策工具/生成器/验证器/复核撰写。

## 独立验证
实现者**不自签 PASS**。本包交独立 Agent 复核（adversarial skeptic，见 adversarial_review.md）后收敛。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
