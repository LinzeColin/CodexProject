# Adversarial review · ADP-S6-P02-T073｜校准 / 技能分数 / Forecast Ledger

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 校准（_bin 边界 0/0.1../1.0/越界/None；has_calibration 是否真门；良校准是否 rigged）；(b) append-only（delete 是否对失败/成功均 raise；raw-list 绕过；_is_failure 阈值；失败是否被误标 success 掩盖）；(c) skill（BSS 公式/负技能诚实/除零；logloss clip/空）；(d) 失败保存（成功与失败均在）；(e) 非空跑（每条款判别控制、verifier 从工具现推）；NOT_DEPLOYED。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=minor）
- **(a) 校准**：`_bin` 各边界正确（0.0→0、0.1..0.9→1..9、1.0→bin9 无第 11 桶、越界 clamp）；IEEE 精确无误配；`has_calibration` 真门（n>0）；负控制 0.35（空 bin3）→ False、calibration_of None。非空跑。
- **(b) append-only**：`delete()` 对失败 f2 与成功 f1 **均 raise**，无其他删除函数；verifier 确认拒删后失败集不变。
- **(c) skill**：BSS=1−mean(model)/mean(ref) 正确；**负技能诚实（worse→−0.3636 不 clamp）**；ref=0→None；空→None。logloss eps clip、空→None。
- **(d)**：`_is_failure` 阈值 0.5 正确；成功与失败均保留；verifier 断言两者在。
- **(e)**：verifier 从工具现推（不读 report JSON），每条款真判别负控制；fixture 充分（4 非空桶、真失败 f2）。
- **NOT_DEPLOYED**：仅 import math（复核时；现另 import hashlib/json 用于哈希链）；无 I/O/网络/时钟/随机。
- **判定**：两验收条款（任何用户可见概率有历史校准 / 失败记录不可删除）**真成立、非空跑/作弊/错**。复核指出 append-only 仅 API 级（raw list 可绕过）——列为 minor latent。

## latent 的主动闭合（复核前哈希链 + 复核后两项）
1. **append-only 仅 API 级、raw-list 绕过**（复核核心 minor）：**复核前已加哈希链** tamper-evidence——`append` 对每记录打 `chain=sha256(prev+seq+core)`，`verify_integrity()` 重算链；**直接 pop 失败 / 把失败改 success 掩盖 → verify_integrity False（可检测）**。故"失败记录不可删除"有**超越 delete() 拒绝的实证牙齿**：删/改任一失败可被检测。verifier 加控制（pop/mutate 失败 → verify_integrity False）。库层为**篡改可检测**，生产强不可删由 D1 append-only（无 DELETE 授权）落地（known_gaps 述）。
2. **`_bin(None)` 抛 TypeError**（复核指出）：**已修** `_bin` try/except 非数值→None；`has_calibration/calibration_of` 对 None bin 返 False/None；`calibration` 跳过 None-bin forecast。verifier 加控制（has_calibration(None)=False 不崩）。
3. **"reliability plots" 只有数据无渲染图**（复核指出，acceptance 不要求图）：本任务出**可靠性数据**（每桶 pred_mean/obs_rate/n）供视图渲染；acceptance row 不需图，非缺陷。known_gaps 述。

## 结论
复核 **CONFIRMED_SOUND**（minor latent 均已闭合）；两验收条款有 load-bearing 判别负控制（未覆盖/None 概率不算校准、delete raise + 哈希链篡改检测、负技能诚实）、非空跑，verifier 从工具现推。append-only 由 delete 拒绝 + **哈希链 tamper-evidence** 双重保障（超越 API 级）；_bin None 优雅处理；reliability 数据齐备。校准/skill 为指标非新模型（运营 MODEL_SPEC 未触）。确定性、零副作用、无 LLM/时钟/随机。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
