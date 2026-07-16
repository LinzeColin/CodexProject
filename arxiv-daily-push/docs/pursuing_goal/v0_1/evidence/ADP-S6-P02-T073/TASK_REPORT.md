# TASK_REPORT · ADP-S6-P02-T073｜实现校准、技能分数与 Forecast Ledger

## 唯一目标（达成）
**长期保存成功和失败，不只展示漂亮案例**：实现 **calibration（可靠性图）+ skill scores（Brier skill/logloss）+ append-only Forecast Ledger**。**任何用户可见概率有历史校准**（其概率桶有历史数据）；**失败记录不可删除**（API 拒删 + 哈希链**篡改可检测**）。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：Brier/logloss/calibration/skill + append-only ledger；每概率有历史校准；失败不可删。
2. **允许修改文件**：`tools/forecast_ledger.py`（新）+ `evidence/ADP-S6-P02-T073/*` + 治理同步。**不改 worker/生产/registry/VERSION**。校准/skill 为**指标**（非新预测模型；复用 T072 回测输出），运营 MODEL_SPEC 未改。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、无时钟/随机。
4. **基线**：main `69ada888`（T072 已合入）；well-calibrated forecast set + model/ref Brier + 含失败的 ledger。
5. **验收**：任何用户可见概率有历史校准（覆盖桶有 n>0；未覆盖桶不算校准=负控制）；失败记录不可删除（delete raise + 哈希链篡改检测=负控制）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/forecast_ledger.py` —— `calibration`（10 桶可靠性图：每桶 pred_mean/obs_rate/n）+ `has_calibration`/`calibration_of`（用户可见概率的桶是否有历史数据）+ `brier_skill_score`（BSS=1−model/ref，**负技能诚实报告**）+ `logloss`（clip 防 log0）+ **append-only Ledger**（`append`[成功与失败均记，哈希链]+`delete`[**raise AppendOnlyError**]+`verify_integrity`[哈希链重算，删/改/重排**检测**]+`failures`/`successes`）。
- `evidence/…/build_forecast_ledger.py`（well-calibrated 40 forecast + model/ref Brier + ledger[1 失败 f2 + 2 成功]）+ `forecast_ledger_report.json` + `test-results/{t073_verify.py, forecast_ledger_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/forecast_ledger_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 任何用户可见概率有历史校准**：可靠性图 **4 个非空桶 pred_mean≈obs_rate**（0.2/0.2、0.5/0.5、0.8/0.8、0.9/0.9——良校准）；覆盖桶概率（0.2/0.5/0.8/0.9）`has_calibration`=True 且 `calibration_of` 返回历史 observed_rate。**负控制（判别力）**：**未覆盖桶概率 0.35 → has_calibration False、calibration_of None**（不自动算校准）。
- **② 失败记录不可删除**：失败 f2 在 ledger；`delete(ledger,"f2")` 与 `delete(ledger,"f1")` **均 raise AppendOnlyError**；拒删后失败集不变、成功与失败均保留。**篡改可检测（哈希链）**：干净 ledger `verify_integrity`=True；**直接 pop 失败 f2**（绕过 delete）→ `verify_integrity` **False**；**把失败改成 success 掩盖**→ `verify_integrity` **False**。
- **③ skill scores（诚实）**：BSS(model)=**0.636>0**（打败 ref）、BSS(equal)=0、**BSS(worse)=−0.364<0（负技能诚实报告不掩盖）**；logloss=0.505。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 40 well-calibrated forecast + model/ref Brier + ledger(1 失败 + 2 成功)。Performance = 实时无回归。无 UI 改动；六主题保留（reliability plots 数据供视图消费）。

## Value / Cost（S6 预测校准）
- **Value**：**诚实的预测问责**——用户可见概率必有历史校准（可靠性图）；技能分数（BSS）对参考量化，负技能诚实报告；**Forecast Ledger 长期保存成功与失败、失败不可删且篡改可检测**——不只展示漂亮案例。为 T074+ Shadow 预测与上线/停止决策提供校准与失败历史。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；**模型调用 0（本地确定性指标，无 LLM）**；人工维护 = 校准/skill/ledger + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：校准为等宽 10 桶（可扩展分位桶）；ledger 库层为哈希链**篡改可检测**，生产强不可删由 D1 append-only（无 DELETE 授权）落地；skill 参考为 base-rate/climatology（可扩展）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = forecast_ledger_report.json。`benchmarks` = forecast_ledger_report.json（BSS/logloss/calibration）。

## 完成声明
```text
Task: ADP-S6-P02-T073
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/forecast_ledger.py(新) + T073 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动；校准/skill为指标运营MODEL_SPEC未改
Tests: forecast_ledger_tests.txt —— 4非空桶pred≈obs;覆盖概率有历史校准未覆盖0.35不算(负控制);失败f2保留delete raise;哈希链篡改(pop/改失败)verify_integrity False;BSS model0.636>0 equal0 worse-0.364<0诚实;logloss0.505;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 校准(可靠性图)+skill(BSS/logloss)+append-only Forecast Ledger(失败不可删+篡改可检测)
Data/Performance/Visual: Data=40 forecast+ledger;Perf=实时无回归；Visual=六主题保留
Value: 诚实预测问责,每概率有历史校准,失败长期保存不可删篡改可检测,负技能诚实报告
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性指标无LLM)；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
