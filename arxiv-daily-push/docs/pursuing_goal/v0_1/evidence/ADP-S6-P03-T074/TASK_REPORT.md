# TASK_REPORT · ADP-S6-P03-T074｜Shadow 来源静默预测

## 唯一目标（达成）
**预测官方源异常静默或采集故障，并区分两者**：对每个官方源预测其当前静默是**异常**（本应已发布）还是**正常**（在其发布周期内），并区分**源异常静默**与**采集故障**（我方抓取器坏了，非源）。**优于简单发布周期基线；误报和人工价值可量化**。开启 S6-P03（窄目标预测 Shadow）。release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：源静默预测（异常静默 vs 采集故障 vs 正常）+ model/baseline + alerts + outcomes；优于简单发布周期基线；误报与人工价值可量化。
2. **允许修改文件**：`tools/silence_predictor.py`（新）+ `evidence/ADP-S6-P03-T074/*` + 治理同步。**不改 worker/生产/registry/VERSION**。指标/统计非新预测模型注册（复用 T073 度量精神）。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP。**SHADOW = dev/shadow 环境预测，0 云成本，生产未触，实时不变**。库层只读、无时钟/随机。
4. **基线**：main `0dd97d27`（T073 已合入）；6 案例 3 类真值（regular abnormal/variable normal/collection failure/regular normal/regular abnormal/variable abnormal）。
5. **验收**：模型优于简单发布周期基线（accuracy 更高、误报率更低）；误报与人工价值量化（数字，源自 outcomes）；区分静默 vs 采集故障（负控制：基线不能区分采集故障）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/silence_predictor.py` —— `cadence`（median interval + MAD 鲁棒离散）+ `simple_cycle_overdue`（**基线**：gap > median interval）+ `classify`（**模型**：fetch 错误→collection_failure；否则 gap > **median + k·MAD**[k=3,鲁棒容忍源自身变异]→abnormal_silence，否则 normal）+ `_baseline_classify`（基线只知 cadence，**不能区分采集故障**）+ `evaluate`（模型与基线对真值打分：accuracy/false_alarm_rate/human_value）。
- `evidence/…/build_silence_predictor.py`（6 案例：REGULAR 每30d/VARIABLE 高变异；含 collection failure 与 variable-abnormal）+ `silence_predictor_report.json` + `test-results/{t074_verify.py, silence_predictor_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/silence_predictor_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 优于简单发布周期基线**：**模型 accuracy 1.0 > 基线 0.667**；**模型误报率 0.0 < 基线 0.5**；模型人工价值 4 ≥ 基线 3。模型的优势来自**两个真实能力**：(a) 鲁棒阈值（median+k·MAD）**不误报自然变异源**（VARIABLE 源 45d 静默属正常，基线误报、模型正确）；(b) **区分采集故障**（fetch 错误→collection_failure，基线误判为静默）。且模型**不过度保守**：VARIABLE 源真异常（80d 远超其变异）仍被模型抓到。
- **② 误报和人工价值可量化**：模型/基线 `false_alarm_rate`、`false_alarms`（计数）、`human_value`（correct_catches×value）**均为源自 outcomes 的数字**（非硬编）。
- **③ 区分官方源异常静默 vs 采集故障**：collection-failure 案例（fetch 错误）**模型分类 collection_failure**；**基线（仅 cadence）不能识别**（判为 abnormal_silence，负控制）；真异常静默被模型抓到。
- **实时无回归**：SHADOW，无生产部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 6 案例（REGULAR/VARIABLE 源，3 类真值）。Performance = 实时无回归。无 UI 改动；六主题保留（alerts 数据供 Shadow 视图消费）。

## Value / Cost（S6 预测校准）
- **Value**：**Shadow 源静默预警**——鲁棒阈值不刷屏（不误报自然变异源）、区分"源真静默"与"我方采集故障"（不同处置）；优于简单发布周期基线，误报与人工价值可量化。为 T075/T076 完整 Horizon Shadow 与上线/停止决策提供 shadow 预测与 outcomes。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；**模型调用 0（本地确定性统计，无 LLM）**；人工维护 = 模型/基线 + 验证编写。经常性云成本 delta = **$0/月（SHADOW，dev 环境，0 云成本，DIR-007 不受影响）**。

## Known gaps
见 `known_gaps.md`：模型为鲁棒阈值（median+k·MAD）——**以召回换精度**（极宽 MAD 理论上可能漏报边界异常，本任务演示模型在真实失败模式[变异误报+采集故障]上的优势且真异常仍被抓，非普遍支配）；k=3 可调；采集故障判据=recent_fetch_errors（真实由抓取日志提供）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（SHADOW，库层）。`data-samples` = silence_predictor_report.json。`benchmarks` = silence_predictor_report.json（model vs baseline）。

## 完成声明
```text
Task: ADP-S6-P03-T074
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/silence_predictor.py(新) + T074 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: silence_predictor_tests.txt —— 模型accuracy1.0>基线0.667误报率0<0.5;误报与人工价值量化(数字源自outcomes);区分collection_failure(模型识别基线不能);变异源正常模型不误报基线误报;变异真异常模型抓到;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Shadow源静默预测(异常静默vs采集故障)+model/baseline+outcomes,优于简单发布周期基线
Data/Performance/Visual: Data=6案例3类真值；Perf=实时无回归；Visual=六主题保留
Value: Shadow源静默预警,鲁棒阈值不刷屏,区分源静默vs采集故障,优于基线,误报人工价值可量化
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性统计无LLM)；经常性成本 0(SHADOW dev环境)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（dev/shadow 环境预测；生产未触，实时无回归，0 云成本）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
