# TASK_REPORT · ADP-S6-P03-T075｜Shadow 主题加速与中央—地方扩散预测

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S6-P03-T075（S6 Prediction & Backtest / S6-P03 窄目标预测 Shadow，size M）
- **release_mode**: SHADOW（dev/shadow env；生产未触；实时 build `b189d3cc0703` == T040 不变；0 云成本）
- **Depends**: ADP-S6-P02-T073（校准+技能分+Forecast Ledger）；复用 T072 rolling backtest、T071 基线思想、T069 可结算目标纪律

## 6 个前置问题
1. **两个 pilot 目标是什么、怎样才「预定义」？** — ACCEL-PILOT（主题 90d 内加速）与 DIFFUSION-A0-A1（中央政策 180d 内扩散到省）。预定义=写死在 `PREDEFINED_TARGETS`（target_id + horizon_days + kind），回测前固定；非预定义（post-hoc）目标被 `is_predefined` 拒。
2. **模型 vs 基线是什么，怎样才算「优于」？** — 模型=条件于净支持信号 `sign(support-counter)` 的桶发生率（Laplace 收缩）；基线=无条件基率（忽略信号）。「优于」=每个 val 窗口模型 Brier < 基线 Brier。
3. **「三个窗口」如何时间安全生成？** — 复用 T072 `rolling_splits`：每起点 O，train=观测≤O，val=观测∈(O, O+horizon]；`assert_no_time_crossing` 逐窗口断言不交叉。3 个滚动起点。
4. **「无确定语气」如何强制？** — surfaced 输出经 `phrase()` 变成对冲概率句；`assert_no_deterministic_tone` 拒绝确定措辞（必然/definitely 等）与 0/1 过度自信概率；所有概率 clamp 到 [0.02,0.98] 严格落在 (0,1)。
5. **support/counter 信号含义？** — ACCEL：support=近月上升计数月数 / counter=饱和信号；DIFFUSION：support=已回声该政策的省份数 / counter=被取代/矛盾的中央事件数。净信号是领先指标。
6. **如何证明「优于基线」非 rigged？** — verifier **独立重算** per-window Brier（自带公式）；**真·特征消融控制**：把 support/counter 置 0 后模型逐字节塌回基线（打平、不 beat），证明优势来自信号而非 harness；**腐化信号探针**：反转 val 信号后模型 Brier 恶化到 0.46–0.56（远差基线），证明模型真依赖信号；**验证窗口含 impurity**（每窗恰1，非可分玩具），模型不完美、赢在聚合。

## 交付物
- **工具** `tools/diffusion_predictor.py`：`PREDEFINED_TARGETS`（2 pilot + horizon）/ `is_predefined` / `fit_model`（桶发生率 Laplace 收缩）/ `predict`（条件概率，clamp 严格 (0,1)）/ `baseline_predict`（无条件基率）/ `rolling_backtest`（复用 T072 split + no-crossing，per-window 模型 vs 基线 Brier + beats_all）/ `phrase`（对冲句）/ `assert_no_deterministic_tone`（拒确定措辞与 0/1）/ `lead_time`。
- **生成器/fixture** `evidence/ADP-S6-P03-T075/build_diffusion_predictor.py`：两 pilot 的 2016+ 构造事件链（各 8 训练 seed 含 2 反例 + 3×3 val）+ 报告（含 surfaced 对冲预测 + lead-time report）。
- **报告** `diffusion_predictor_report.json`。
- **known_gaps.md**：诚实披露（构造 fixture 非真实语料回测、窄条件模型、A2 扩散未建 pilot、无真实 settled 精度、无 CI）。
- **独立对抗复核** `adversarial_review.md`。

## 验收（三条款，verifier 独立重算，PASS）
证据：`test-results/diffusion_predictor_tests.txt`（ACCEPTANCE = PASS，exit 0），verifier `test-results/t075_verify.py`。

1. **三个窗口优于基线** — 两 pilot 各 3 窗口（**验证窗口含 impurity，非可分玩具**），verifier **自带 Brier 公式重算**每窗口：
   - ACCEL-PILOT（h90d，基率~0.5）：model 0.163 / 0.179 / 0.161 vs baseline 0.250 / 0.258 / 0.250 → 3/3 beat。
   - DIFFUSION-A0-A1（h180d，基率~0.6）：model 0.169 / 0.146 / 0.137 vs baseline 0.278 / 0.262 / 0.257 → 3/3 beat。**两 pilot Brier profile 相异**（不同 fixture），非 clone。
   - **真·特征消融控制**（load-bearing，非空跑）：把 support/counter 置 0 后模型**逐字节塌回基线**（ablate==base，打平、不 beat；数学恒等 bucket-0 率=glob）→ 证明优势来自信号，非 harness。复核用 monkeypatch 注入非信号特征验证该控制会 fail（非空跑）。
   - **腐化信号探针**（load-bearing）：反转 val 信号后模型 Brier 恶化到 **0.46–0.56**（远差基线）→ 证明模型真依赖信号（信号错就输）。
   - **验证含噪**：每个 val 窗口恰 1 个 impurity（6/6 窗口），模型不完美、赢在聚合；非可分玩具。
2. **目标和 horizon 预定义** — 两 pilot ∈ `PREDEFINED_TARGETS` 且 horizon 为固定整数；**负控制（两处）**：post-hoc 目标 `is_predefined("POST-HOC-CHERRY-PICK")` False；`rolling_backtest(..., target_id="POST-HOC-CHERRY-PICK")` **raise** 拒绝回测。
3. **无确定语气** — 所有 surfaced 概率严格 (0,1)（clamp [0.02,0.98]，0/1 永不 surface）；hedged 句通过 gate；**负控制**：6 条确定措辞（必然/百分之百/势必/毫无疑问/definitely/inevitable）与 0/1 概率均被 `assert_no_deterministic_tone` **拒**。
- **时间安全负控制**：train 样本观测在 origin 之后的 split 触发 `assert_no_time_crossing` raise。
- **lead-time**：ACCEL 90d、DIFFUSION 180d 正确；**可复现**：rolling_backtest 两次逐字节一致。

## 实时未回归
`/build.json` 实测 `build_id=b189d3cc0703`（== T040），schema `cn_v0_3`。SHADOW 库层任务，无 worker/D1/R2/cron 改动。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 行读 0 / 写 0；R2 字节 0 / 操作 0；model_calls 0；recurring cloud 0（SHADOW dev env）；人工维护=模型/基线/生成器/验证器/复核撰写。

## 独立验证
实现者**不自签 PASS**。本包交独立 Agent 复核（adversarial skeptic，见 adversarial_review.md）后收敛。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
