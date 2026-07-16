# Adversarial review · ADP-S6-P01-T071｜历史频率 + 季节性统计基线

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。**特别核验：这是 v0_1 首个统计模型，NOT_DEPLOYED，MODEL 治理是否诚实充分。**

## 攻击向量
(a) 基线正确（frequency==base rate？Laplace 是否恒 [0,1]？退化历史/未见月/n=0/除零）；(b) 可重跑（benchmark 是否无 clock/random/dict-order；报告是否 lambda-free 可 JSON 化使 report==report2 有意义）；(c) 每目标≥1基线（空历史目标是否被静默当真基线）；(d) 门（may_develop_advanced 是否真判别、可否被 always-True 作弊）；(e) 有意义/非空跑（季节性打败频率是否真信号无泄漏、verifier 是否从工具现推）；NOT_DEPLOYED + MODEL 治理诚实性。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
（复核者注：会中文件churn——初读到 no-history 硬化前的弱版[benchmark 硬编 has_reproducible_baseline=True 无 n_history、无 G0]；结论对**当前在盘鲁棒版**得出：baselines.py md5=5fad09e1、verifier=3d1bfb9d、build=5fa14b6f。）
- **(a) 正确**：frequency==实际 base rate（0.375=3/8）；Laplace `(events_m+α·glob)/(n_m+α)` 对 空/全0/全1/malformed/未见月/n=0/α=0 **恒 [0,1]**；无除零（n=0→0.0；空 eval→metrics None）；未见月回退平滑全局非硬 0/1。
- **(b) 可重跑**：报告纯数字/布尔/dict——`predict` lambda **留在 baseline 内不入报告**，故 `report==report2` 是真内容比较；完全 JSON 可序列化；工具零 import、无 clock/random/network/写。
- **(c) 每目标**：含历史目标得 freq+seas + 有效 metrics；**空历史 G0 正确 `has_reproducible_baseline=False`**（不静默当真）。
- **(d) 门**：真判别——G1→True；G0（无历史，在报告内）→False；缺席/未知/空 baselines→False。复核者**模拟硬编 always-True benchmark 证 G0 控制抓到回归**。
- **(e) 有意义**：G1 上 seasonality Brier 0.08252 < frequency 0.265625；训练(2020-2022)与 eval(2023)**时间不交叉无泄漏**；verifier 从工具现推并**独立重算 base rate**（不信报告 JSON）。
- **NOT_DEPLOYED + MODEL 治理**：实时 build b189d3cc0703 不变；运营 MODEL_SPEC/formula_registry **未触**；**in-evidence MODEL card 诚实、充分、引用现存工件**——对 NOT_DEPLOYED 基线足够（无需注入运营注册）。
- **判定**：两验收条款（每目标≥1可重跑基线 / 无基线不得开发高级模型）**真成立、非空跑/作弊/错**；MODEL 治理诚实充分。列 3 项**非致命** latent。

## 主动硬化（复核前，会中已做）
- **空历史 = 无可重跑基线门**（前置硬化）：原 `benchmark` 硬编 `has_reproducible_baseline=True`——空历史目标会得无意义 rate-0.0 基线且门放行，**违反「无基线不得开发高级模型」**。已改：`benchmark` 计 `n_history`，`has_reproducible_baseline = n_history >= min_history(=1)`；加 fixture G0（无历史）+ verifier 负控制（G0 门拒）。复核者据此证门真判别。

## 残留（复核指出，非致命，均不可达/恰当）
1. `may_develop_advanced` 会信任**手工构造**声称 has_reproducible_baseline=True + 非空 baselines 的零历史条目——但 `benchmark`（唯一诚实生产者）**永不产出**此组合，**管线内不可达**。
2. verifier `WITH_HISTORY` 硬编 G1/G2——对本 fixtures 恰当；新增含历史目标需扩展。
3. 空历史目标仍带退化 rate-0.0 baselines dict，但 `has_reproducible_baseline=False` 阻止门当真——**无作弊**。

## 结论
复核 **CONFIRMED_SOUND**；两验收条款有 load-bearing 判别负控制（空历史 G0 门拒[变异证真判别]、季节性打败频率[真信号无泄漏]）、非空跑，verifier 从工具现推独立重算。前置硬化空历史门（已证真判别）。首个统计模型 MODEL 治理诚实（in-evidence MODEL card 充分，运营 MODEL_SPEC 门控于 promotion 不触）。确定性、零副作用、无 LLM/时钟/随机。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
