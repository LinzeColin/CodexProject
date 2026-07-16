# Adversarial review · ADP-S6-P03-T074｜Shadow 来源静默预测

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。**特别核验"优于基线"是否为 rigged fixture。**

## 攻击向量
(a) 优于基线是否真实非 rigged（robust 阈值是否真优势、模型是否某些输入更差[宽阈值漏真异常]、是否 cherry-pick 单案例）；(b) 误报/人工价值是否真算（除零、never-alarm 是否 0 catch、能否 game 高）；(c) 静默 vs 采集故障区分是否真（fetch+overdue 谁胜、基线能否偶然对、cadence 逻辑）；(d) cadence 数学（median/MAD/空/单/乱序/重复/负 gap）；(e) 非空跑/负控制、verifier 从工具现推；SHADOW/无生产。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
（复核者注：初读到 5-案例旧版；结论对**当前 6-案例在盘版**得出。）
- **(a) 优于基线=真非 rigged**：模型 acc 1.0 vs 基线 0.667(4/6)，来自**两个真机制**：(案例2) 变异感知阈值 median+3·MAD 不误报 VARIABLE 源 gap45（在其观测最大间隔 60 内→诚实标 normal，基线过度告警）；(案例3) fetch 错误信号识别采集故障。**案例6**（VARIABLE gap80>阈值65→异常，模型也抓）**直接反驳"宽阈值漏真静默"**。复核者**扫描 gap40-80**：模型仅在**源自身变异内**(≤60)保持 normal、gap66+ 翻异常——故**诚实标注集上模型不输基线**（其"漏"对应本不该标异常的 gap）。标准 robust 异常检测技术，非侥幸。
- **(b) 误报/人工价值真算**：`false_alarm_rate=fa/normal_total`（真除零守卫，fixture 有 2 normal 案例故真被行使）；`human_value=correct_catches·value`（never-alarm→0 catch→0 value 正确反映）；game 高需接受误报，而 verifier 要求 **human_value≥baseline AND false_alarm_rate<baseline**。从工具现推非 report JSON。
- **(c) 区分真**：`classify` 先查 recent_fetch_errors>0→collection_failure（即便同时 overdue——fetch 坏时无法判源是否真静默，此为诚实保守判断）；模型侧控制实质。
- **(d) cadence 数学正确**：median(奇偶)/MAD/乱序/重复/空/单历史(→None→保守 normal)/负 gap 均正确无崩溃。
- **(e)**：6 案例 3 类真值判别负控制齐；verifier 从工具现推不信 report。确定性、零 import IO/网络/时钟/随机；build 仅写证据 JSON；**生产未触→SHADOW-clean**。
- **判定**：两验收条款（优于简单发布周期基线 / 误报与人工价值可量化）+ 区分静默 vs 采集故障**真成立、非空跑/作弊/错、非 rigged**。列 latent（非致命）。

## latent 的主动闭合（2 项 + 3 项披露）
1. **line58 基线 collection_failure 控制 tautological**（复核指出）：`_baseline_classify` 结构上不能返回 collection_failure，故 `==collection_failure` 永假、该守卫永不触发（空跑）。**已修**：改为**非空跑**——断言基线**主动误判**采集故障为 `abnormal_silence`（`b_cf==truth` 失败 + `b_cf!="abnormal_silence"` 失败），一个返回 collection_failure 或 normal 的基线都会失败。这才是模型的真优势（基线把我方 fetch 故障错当源静默）。
2. **无模型输给基线的案例 / 边界召回**（复核指出可加固）：**已加边界召回探针**——VARIABLE 源（阈值 median35+3·MAD10=65）在 **gap66→异常、gap65→normal**，证明模型阈值**不盲目宽**、恰在源自身变异边界翻转（非过度保守亦非过度告警）。
- **(#3 披露)**：模型严格 human_value 优势(4>3)仅来自 collection_failure 案例；纯静默检测 human_value 打平——verifier 用 `≥` 且 accuracy/误报的严格胜来自真机制(案例2)，故无碍。
- **(#4 披露)**：k=3 阈值较宽（本源约 2×median 才告警）——**可调选择非 bug**，known_gaps 述精度/召回权衡。
- **(#5 披露)**：recent_fetch_errors 是采集故障的信号特征（检测近乎直接）——但这是**正确的现实世界信号**（源健康账/抓取日志），非作弊。

## 结论
复核 **CONFIRMED_SOUND**；两验收条款有 load-bearing 判别负控制（基线误报变异源、基线误判采集故障[已改非空跑]、模型抓真异常 + 边界召回）、非空跑，verifier 从工具现推。"优于基线"经 gap 扫描证明为**真机制非 rigged**。2 项 latent 主动闭合（tautological 控制改非空跑、加边界召回探针）+ 3 项诚实披露（human_value 来源、k 权衡、fetch 信号）。确定性、零副作用、无 LLM/时钟/随机。SHADOW（dev 环境，生产未触，实时 build b189d3cc0703 == T040 不变，0 云成本）。判定：**可交独立验证 / SHIP**。
