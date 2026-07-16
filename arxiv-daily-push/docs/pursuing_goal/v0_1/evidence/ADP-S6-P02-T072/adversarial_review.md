# Adversarial review · ADP-S6-P02-T072｜2016+ Rolling-origin Backtest

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) ≥3窗口（是否退化/空窗仍计数）；(b) 训练/验证时间不交叉（边界 obs==origin / obs==val_end / 之后；是否有样本同属两集；泄漏 guard 是否真作用于每 train 集；日历/闰年）；(c) 可重跑（无 clock/random/dict-order；manifest 稳定且内容敏感、是否碰撞）；(d) 基线拟合完整（只用 train 拟合、只在 val 评分；季节性 Brier 改善是真信号还是 rigged）；(e) 非空跑（每条款判别控制、verifier 从工具现推）；NOT_DEPLOYED。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
- **(a) ≥3窗口**：真实——每起点一窗口(3)，非退化（train_n=[9,12,15] val_n=[3,3,3]）；空窗会以 None Brier 暴露被抓。
- **(b) 时间不交叉**：`train=obs<=O` / `val=obs∈(O,O+h]` 为**互斥 if/elif**，无对象同属两集（exact-origin→train、exact-val_end→val）；verifier 独立重算时序谓词 + 对象身份不相交 + 逐 train 集 T070 guard。**负控制均 RAISE**（起点后 train / 起点前 val）；`datetime.timedelta` 闰年正确。
- **(c) 可重跑**：确定性（无 clock/random；manifest `sort_keys=True`）；两次一致；改 horizon/单 label 均翻 manifest；verifier 比对**结果+manifest**。
- **(d) 基线完整**：仅 `sp["train"]` 拟合、仅 val 评分；复核者**手算三个季节性 Brier(0.013889/0.008889/0.006173)** 证改善为 Laplace 平滑随三月历史收敛(0.833→0.867→0.889)的**真泛化信号**，非 fixture 造假。
- **(e) 非空跑**：每条款有判别负控制；verifier 从工具（`RB.run_backtest/rolling_splits`）现推**不读 report JSON**（import build 模块不跑 main）；fixture 充分（2016-2022，21 结果，真季节模式）。
- **NOT_DEPLOYED**：grep 无 today/now/random/网络/写（仅 datetime.date/timedelta on 传入日期）。
- **判定**：三验收条款（≥3窗口 / 训练验证时间不交叉 / 可重跑）**真成立、非空跑/作弊/错**。列 3 项**非致命** latent。

## latent 的主动闭合（3 项）
1. **run_manifest 漏 min_history**（复核指出）：仅差 min_history 的两次运行会碰撞同 manifest（trainable 翻转但 full result 不同）。**已修**：`run_manifest` 纳入 `min_history` + `trainable`；verifier 加控制（改 min_history → manifest 不同，实测 `bt:06d6397caf6b3ab4` 稳定）。
2. **`_d()` 对日历非法日（2019-02-30）抛 ValueError 而非 None**（复核指出，`_parse_date` 只查 day<=31）：**已修**：`_d` try/except ValueError→None；verifier 加控制（2019-02-30 outcome 既不入 train 也不入 val，不崩溃）。
3. **T070 泄漏 guard 无专属负控制**（仅 assert_no_time_crossing 有）：**已加专属控制**——train 集含未来观测样本(2025-01-01)→`assert_no_leakage` **RAISE**（独立于 crossing 控制）。

## 结论
复核 **CONFIRMED_SOUND**；三验收条款有 load-bearing 判别负控制（crossing 样本 RAISE、manifest 内容敏感、季节性 Brier 真泛化[手算证]）、非空跑，verifier 从工具现推。3 项 latent 主动闭合（manifest 纳 min_history+trainable、_d 日历非法日不崩、T070 guard 专属控制）。复用 T071 基线模型（非新模型，运营 MODEL_SPEC 未触）+ T070 泄漏 guard + T056 日期解析。确定性、零副作用、无 LLM/时钟/随机。实时无回归（live build_id b189d3cc0703 == T040）。**开启 S6-P02**。判定：**可交独立验证 / SHIP**。
