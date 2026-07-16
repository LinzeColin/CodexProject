# TASK_REPORT · ADP-S6-P01-T069｜定义预测目标、Outcome Rule 与事件标签

## 唯一目标（达成）
**先定义什么算发生，再训练任何模型**：建立预测**目标 catalog + horizon + settlement rules + 事件标签**。每个目标只有能**由未来官方证据（A0/A1 原文）客观 0/1 结算**才可入回测；**模糊/主观目标一律拒绝、不得进入回测**。开启 Stage S6（预测、校准与失败历史）。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：target catalog + Outcome Rule（结算规则）+ 事件标签；可官方结算才入回测，模糊拒绝。
2. **允许修改文件**：`tools/prediction_targets.py`（新）+ `evidence/ADP-S6-P01-T069/*` + 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、**无时钟**（日期由调用方传入，datetime 仅做传入日期的算术）。
4. **基线**：main `7cc13ba7`（T068 已合入，Stage S5 收尾）；catalog 含 settleable + ambiguous 混合、官方/媒体/未来证据。
5. **验收**：每目标可由未来官方证据结算（definite 0/1；官方-only + observed_at 窗口防泄漏）；模糊目标不得进入回测（拒绝 + settle 拒算）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。
7. **模型路由**：S6 为模型领域（T2/T3）。**本任务为预测目标/结算规则的定义（确定性 Outcome Rule，非训练模型/公式）**，故不动 MODEL_SPEC/formula_registry；真正统计/ML 模型自 T071（基线）起再登记。

## 交付物
- `tools/prediction_targets.py` —— `make_target`（target_id/description/horizon_days/subject/settlement）+ SETTLEMENT_TYPES（`official_doc_exists`/`status_transition`/`count_at_least` 三种**客观谓词**，各声明必填字段）+ `is_settleable`（已知客观谓词 + 全部必填非空非主观 + 有限正 horizon）+ `admit_targets`（拆 admitted/rejected 带原因）+ `settle`（对**官方**证据在 [origin, origin+horizon] 窗口内结算 → definite 0/1，或窗口未过 `pending`；忽略媒体与窗口外，防泄漏；对不可结算目标 **raise**）。
- `evidence/…/build_prediction_targets.py`（6 目标：3 settleable[official_doc_exists/count_at_least/status_transition] + 3 ambiguous[主观谓词/空字段/无 horizon]；官方匹配/媒体 look-alike/未来官方证据）+ `prediction_targets_report.json` + `test-results/{t069_verify.py, prediction_targets_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/prediction_targets_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 每目标可由未来官方证据结算**：G1/G2/G3 全 admitted 且 settleable；官方结算给 **definite** label——G1 官方匹配=1 / 媒体或未来-only=0；G2 两次官方=1 / 一次(窗口过)=0；G3 状态转 revoked=1；**窗口未过且无匹配→pending**（不臆断）。
- **② 模糊目标不得进入回测**：B1（主观谓词 is_important）/B2（topic 空）/B3（horizon 0）**全 rejected、不在 admitted**；`settle` 对三者**全 raise**（永不可回测）。
- **③ official-only + 无泄漏（负控制/判别力）**：**媒体 look-alike**（authority≠A0/A1）在窗口内**不结算 1**；**未来观测的官方匹配文档不泄漏**（in-window=1，after-window=0）。**边界**：恰在窗口末日观测→1；末日后一天→不泄漏；**malformed/None observed_at 不崩溃不误 1**。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 6 目标 catalog（3 settleable + 3 ambiguous）+ 官方/媒体/未来证据。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S6 预测校准）
- **Value**：**可回测预测的诚实地基**——先把「什么算发生」定义成**可由官方原文客观结算**的 Outcome Rule，模糊目标一律挡在回测门外；official-only + observed_at 窗口从源头防未来泄漏。为 T070（快照/泄漏防线）、T071（基线）、T072（Rolling-origin Backtest）提供确定性目标与标签。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0（确定性结算规则，非训练模型）；人工维护 = catalog + 结算规则 + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：settlement 谓词为 3 类客观类型（可扩展但每新增须保持可官方结算）；label SQL 由部署阶段将谓词编译为 D1 查询（本任务出确定性 Python 结算与契约）；真正统计/ML 模型自 T071 起，届时登记 MODEL_SPEC/formula_registry。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = prediction_targets_report.json。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S6-P01-T069
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/prediction_targets.py(新) + T069 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: prediction_targets_tests.txt —— G1/G2/G3 settleable官方结算definite(官方1/媒体0/未来不泄漏/未过pending);B1/B2/B3模糊全rejected且settle raise;official-only(媒体不结算)+observed_at窗口防泄漏(in-window1/after0/边界末日1末日后不泄漏/malformed安全);实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 预测目标catalog + Outcome Rule结算规则 + 事件标签(可官方结算才入回测,模糊拒绝)
Data/Performance/Visual: Data=6目标+官方/媒体/未来证据；Perf=实时无回归；Visual=六主题保留
Value: 可回测预测的诚实地基,先定义什么算发生,official-only+observed_at防泄漏
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0(确定性结算规则)；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
