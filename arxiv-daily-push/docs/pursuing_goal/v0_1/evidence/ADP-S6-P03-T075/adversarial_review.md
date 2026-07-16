# Adversarial review · ADP-S6-P03-T075｜Shadow 主题加速与中央—地方扩散预测

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/rigged fixture/vacuous 控制/误导），非确认。**两轮**：第一轮 **HOLE_FOUND**（致命：headline 控制是 tautology），修复后第二轮 **CONFIRMED_SOUND**。

## 攻击向量
(a) 「三窗口优于基线」是否 rigged fixture（可分玩具 / 模型能否输 / 基线是否稻草人 / 特征消融是否真证因果）；(b) 目标/horizon 是否真预定义还是 post-hoc；(c) 无确定语气是否真强制还是 cosmetic（0/1 能否 surface、词表是否漏）；(d) 时间安全/泄漏；(e) vacuous/tautological 控制、verifier 是否独立重算 Brier；(f) 两 pilot 是否真独立还是 clone、support/counter 是否真输入、lead-time；(g) SHADOW/纯度（网络/时钟/随机/生产副作用）。

## 第一轮：HOLE_FOUND（致命-对-保证）
- **主洞（fatal-to-assurance）**：`t075_verify.py` 的 headline「特征消融」控制是 **tautology**——ablated 行与 baseline 行**表达式完全相同**（都调 `baseline_predict`），`ablated < b` 即 `b < b` **恒 False**、dead code；它**没有**把 signal-blind 模型喂给 `predict()`。故「优势来自信号而非 harness」是**断言而非证明**。三条字面验收仍成立（模型确实优于基线），但复核者明确指出这是**载荷控制变装饰**，**必须在 commit 前修**。
- 次要（misleading/latent）：①验证窗口 **100% 可分**（impurity 只在训练期），known_gaps「非可分玩具」只对训练率成立、对验证沉默——复核者构造含噪窗口使模型 **Brier 0.49 输给基线 0.25**；②两 pilot **逐字节 clone**（Brier 全等），非独立证据；③`rolling_backtest` 从不调 `is_predefined`（post-hoc 目标只在 build() 触 KeyError）；④`_DETERMINISTIC` 词表 porous（百分之百/势必/毫无疑问/inevitable/bare 一定 漏）。
- 判定：字面验收 PASS 但保证被削弱，**HOLE 必修**。

## 修复（commit 前，逐项闭合）
1. **主洞（真·特征消融）**：verifier 改为把 support/counter **置 0**（`_blind`）后**重拟合并预测**，断言 `abl == baseline`（打平、不 beat）。**数学恒等**：net_signal 全 0→单桶 0，其率 `=(Σlabel+α·glob)/(n+α)=glob`，故必等基线——非巧合。复核第二轮**monkeypatch 注入非信号特征**（日期奇偶，blinding 不清零）→ `abl≠base` 触发断言，证**非空跑**。
2. **可分玩具→含噪验证**：两 fixture 重写，**每个 val 窗口恰 1 impurity**（6/6），模型不完美、赢在聚合。新增**腐化信号探针**（保留真模型、只反转 val 信号→模型退化到 **0.46–0.56** 远差基线），证模型真依赖信号。
3. **clone→独立**：两 pilot 换不同 fixture（基率 ~0.5 vs ~0.6、val 5 vs 6、horizon 90 vs 180），Brier profile 相异、**零共享窗口**；verifier 加 clone-check 断言两 profile 不等。
4. **预定义强制**：`rolling_backtest(..., target_id=)` 对非预定义目标 **raise ValueError**；build() 传 `target_id=tid`；verifier 加第二负控制。
5. **词表硬化**：`_DETERMINISTIC` 增 必定/必将/一定/势必/注定/铁定/百分之百/毫无疑问/无疑/十拿九稳/板上钉钉/100%/inevitable/assured/certain to/sure to 等（`phrase()` 在 clamp 极值 2%/98% 仍通过，无 100% 误报）。

## 第二轮：CONFIRMED_SOUND
复核者**独立重执行**逐项验证修复为真非 cosmetic：
- **(1) 特征消融真非空跑**：证 bucket-0 率=glob 为**数学恒等**（任意 α，6 窗口 identity_holds=True）；monkeypatch 注入非信号特征→控制 fire。**过**。
- **(2) 腐化探针真非空跑**：逐窗口反转 Brier 0.46–0.56 全输基线；强制「偷看 label 忽略信号」的作弊模型→反转成 no-op、`inv<b` 断言 fire。**过**。
- **(3) 非 clone**：ACCEL vs DIFFUSION Brier profile 相异、交集为空、基率/val 大小/horizon 皆不同。**过**。
- **(4) 模型能输**：复核构造 3-impurity 窗口模型 **0.4625 输** 基线 0.25；聚合胜诚实。
- **(5) 预定义**：`rolling_backtest` 拒 post-hoc（raise）。**过**。
- **(6) 词表硬化无回归**：4 条真 surfaced 句仍过、6 markers 拒。**过**。
- **(7) 无新 vacuous 控制**：6 窗口独立验证 train≤origin<val≤val_end 不交叉、时间交叉负控制仍 fire、可复现、纯度干净（无网络/now/随机/subprocess/os.environ，仅确定性 timedelta）；git 仅新增 evidence 目录 + 新工具，**生产/live-build 未触，SHADOW intact**。

### 复核第二轮指出的 1 处 latent（已闭合）
- **DIFFUSION 窗口2（@2019-06-30）实为 0 impurity**（6 案例全可分，Brier 异常低 0.0402），与 `; 1 impurity` 注释及「每个 val 窗口都含 impurity」的 docstring **矛盾**——是文档自述的事实不准。**已闭合**：把 2019-10-15 改为 impurity（4,2,0：省级回声但中央政策被取代），该窗口 Brier 0.0402→**0.146**（仍 beat 基线 0.262），现 **6/6 窗口恰 1 impurity**、与自述一致。
- 词表 porous 残留（`certain to`/`sure to`/十拿九稳 等，第二轮又补）——但复核明确**不可达**（surfaced 文本仅来自硬编码 `phrase()`），语气安全主防线是 `phrase()`+clamp，词表是纵深第二层；known_gaps 已如实披露。

## 结论
两轮复核：**HOLE_FOUND（vacuous 载荷控制）→ 修复 → CONFIRMED_SOUND**。三条验收（三窗口优于基线 / 目标+horizon 预定义 / 无确定语气）成立，两条替换控制（真·特征消融 + 腐化信号探针）**load-bearing 且经注入证明非空跑**，两 pilot 独立、验证含噪（6/6 恰 1 impurity）、模型可输赢在聚合、预定义两处强制、词表硬化。确定性、零副作用、无 LLM/时钟/随机。SHADOW（dev 环境，生产未触，实时 build b189d3cc0703 == T040 不变，0 云成本）。判定：**可交独立验证 / SHIP**。
