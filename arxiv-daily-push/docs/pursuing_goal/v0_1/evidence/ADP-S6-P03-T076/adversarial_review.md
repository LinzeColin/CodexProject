# Adversarial review · ADP-S6-P03-T076｜完整 Horizon Shadow + go/stop 决策

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找橡皮图章门/rigged 输入/vacuous 控制/度量作弊/误导），非确认。**复核结论 CONFIRMED_SOUND**（一项非致命 latent 已闭合）。

## 攻击向量
(a) go/stop 门是否橡皮图章（能否真 STOP、4 个控制是否各翻转恰一准则且非空跑）；(b)「持续技能」是否诚实（aggregate>0 且 min每窗>0 是否忠实「为正且稳定」、单个近零/负窗口能否溜过）；(c) 校准度量是否诚实选择（ECE vs max-per-bin 是否 metric-shopping、max-bin 是否披露、失校准控制是否真 fail ECE）；(d) 领先价值是否真实（correct/误报是否真统计、能否 game、零 lead 控制是否非空跑）；(e) vacuous/tautological 控制、verifier 是否独立重算 BSS 与 ECE；(f) 组合是否诚实（是否用真 T074+T075 输出、6 窗口是否真 T075 pilot）；(g) SHADOW/纯度 + GO 是否只是建议无生产动作。

## 复核方法与结论：CONFIRMED_SOUND
复核者**读全部文件 + 跑实验**：自带公式重算 per-window BSS 与 ECE、**monkeypatch 破坏门逻辑跑 verifier 全体**、试图强制错误决策。
- **(a) 门真判别非橡皮图章**：monkeypatch `release_decision` 恒 GO → verifier exit 1 抓住全部 4 个 STOP 控制；恒 STOP → 真实 shadow→GO 断言 fail。BSS≈−4e-7 的近负窗口与 BSS=0 的零技能窗口（`min>0` 严格）都正确 STOP。4 控制各翻转恰一准则，verifier 用 `==` 断言 `failed_criteria`。
- **(b) 持续技能诚实**：`skill_ok = aggregate>0 且 min(每窗BSS)>0`（line38）。独立重算 per-window BSS [0.35,0.307,0.357,0.392,0.445,0.467] 全>0、aggregate 0.386933 逐位匹配报告。patch 掉 sustained 的每窗要求 → verifier fail（控制 a 抓住）。单个近零/负窗口无法溜过。
- **(c) 校准度量合法非 metric-shopping**：重算 ECE 0.092526（匹配）、max-bin 0.333333。max-bin 在报告与 known_gaps **双重披露**；0.333 集中在稀疏低桶（bin2 n6/bin3 n2，预测 24–33% 但 0 事件=良性方向性过预测），而两个稠密高概率桶（bin7 n12 err0.017/bin8 n8 err0.084，占 20/33）校准良好。ECE 是校准领域标准度量，选它而非噪声主导的 MCE 可辩护且已披露。失校准控制（pred0.9/obs0.3）真产 ECE0.6→STOP。
- **(d) 领先价值真实非编造**：net=19−5=14 由 shadow 重算（扩散 pilot 样本外 prob>0.5 的 15 正确+5 误报 + T074 来源静默 4 真捕获，`SP.evaluate` correct_catches=4）。零 lead / 无净价值控制都仅在 lead 准则 STOP。
- **(e) 无 vacuous 控制**：verifier 自带 BSS 与 ECE 公式（line39,44）与工具比对，从不信报告；每个控制经破坏门验证为非空跑。
- **(f) 组合诚实**：`gather_shadow` 用真 `bdp.PILOTS`（T075 fixture）+ 真 `bsp.CASES`（T074），重跑真 `fit_model/predict/baseline_predict` + `rolling_splits`；独立重算 6 窗口逐位匹配。33 forecasts=15 ACCEL+18 DIFFUSION，滚动窗口互斥全样本外（无校准泄漏）。known_gaps 透明披露 T074 进领先价值维度非 Brier-skill 维度。
- **(g) 纯净确定性无生产副作用**：依赖链无 network/clock/random（仅 rolling_backtest 对传入日期做 timedelta）。报告 hash 稳定、与磁盘一致。GO 是纯建议对象无部署路径；live build b189d3cc0703 == T040 未触（T076 无任何生产代码）。

## latent 的主动闭合（1 项，非致命）
- **`closeout(...)` 默认 tol=0.2 与 `calibration_assessment`(line45)/全部文档/known_gaps 规定的 tol=0.15 不一致**（复核指出）：真实证据路径与 verifier 都**显式传 tol=0.15**，故 T076 的 GO 决策在文档化的 0.15 门计算、不受影响（真实 ECE 0.093 两者都过）。但未来调用者用 `closeout()` 默认会静默拿到更松的门（复核构造 ECE≈0.183 的样本在 0.15 STOP 但 0.2 GO）。**已闭合**：`closeout` 默认改为 `tol=0.15`，与 `calibration_assessment` 及文档一致；重跑 verifier 仍 PASS、报告不变（显式 0.15）。

## 结论
复核 **CONFIRMED_SOUND**：go/stop 门真能 STOP（4 控制各翻转恰一准则、经 monkeypatch 破坏验证非空跑）、「持续技能」是「为正且稳定」的忠实严格读法（每窗 BSS>0）、校准 ECE 度量选择已披露且可辩护（max-bin 作 diagnostic）、领先价值计数真实、verifier 独立重算 BSS 与 ECE。1 项非致命 latent（closeout 默认 tol 不一致）已闭合。确定性、零副作用、无 LLM/时钟/随机。SHADOW（dev 环境，生产未触，实时 build b189d3cc0703 == T040 不变，0 云成本；**GO 是建议非动作**，实际展示仍受 S6 Exit Owner Gate 门控）。判定：**可交独立验证 / SHIP**。
