# TASK_REPORT · ADP-S4-P02-T045｜按用户价值选择 A0 回填 Cohort

## 唯一目标（达成）
**先覆盖高价值中央/国家级领域，不按 Registry 顺序盲目全开**。交付 priority model、cohort manifest、expected benefit。**每个 source 有权威角色、历史起点、预期文档类型和停止规则。**

## 六个开始前问题（已回答）
1. **唯一目标**：按用户价值选 A0 回填 cohort；每源有权威角色/历史起点/预期文档类型/停止规则；不盲开。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/cohort_selector.py, COHORT_SELECTOR_SPEC.md}` + 本证据包（cohort_manifest/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；**不执行回填、不自签晋级**（Owner cohort 门）。NOT_DEPLOYED。
4. **基线**：main `49c470ec`（T044 收尾 S4-P01）；候选 = S3-P02 已证明的 A0 源。
5. **验收**：每个 source 有权威角色、历史起点、预期文档类型和停止规则。
6. **回滚**：`git revert <sha>`（纯提案，生产未变更）。

## 交付物
- `tools/cohort_selector.py` —— `value_score`（0.4 domain_value + 0.3 coverage_gap + 0.3 stability）+ `stop_rule` + `select_cohort`（**按价值降序、非 registry 顺序**；每 member 含 authority_role/history_start/expected_doc_types/stop_rule/expected_benefit；live 受阻源 deferred）。
- `COHORT_SELECTOR_SPEC.md` + `evidence/.../cohort_manifest.json`。

## 验收结果（实测，见 test-results/cohort_tests.txt，ACCEPTANCE = PASS，exit 0）
- **每 source 有权威角色/历史起点/预期文档类型/停止规则**（+expected_benefit）：**5 个 member 全齐**。
- **按价值非 registry 顺序**：value 降序 **[gov-cn-policy 1.0 > gov-cn-fagui 0.965 > stats-gov 0.9 > cac-gov 0.88 > ndrc-gov 0.865]**；top = 最高价值中央源（国务院政策）。
- **不盲开**：live 受阻的 `nda-gov`（T036 TLS/JS-shell）**deferred**（记 deferred_reason），不入 Wave 1。
- **priority model + cohort manifest + expected benefit** 齐备。

## Data / Performance / Visual
Data = Wave-1 cohort manifest（5 源 + 1 deferred）。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S4 2016+ Expansion）
- **Value**：十年回填**从最有价值处开始**——按用户价值选中央/国家级 A0 源，每源明确权威角色/历史起点/预期文档类型/**停止规则**（回填至起点即停 + realtime 背压守护），受阻源 deferred 而非盲开；扩张有序、可停、有预期收益。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = cohort 提案。经常性云成本 delta = $0/月。**执行（T046）+ 云成本待 Owner cohort 门 SCALE 后。**

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED + Owner 门待决（不执行回填/不自签）；value 输入为结构性评分（接 T043/T044 校准）；history_start 源级默认；nda-gov deferred；expected_doc_types 代表性。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke` —— N/A。`data-samples` = cohort_manifest.json。

## 完成声明
```text
Task: ADP-S4-P02-T045
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/cohort_selector.py + COHORT_SELECTOR_SPEC.md + T045 证据包（cohort_manifest/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: cohort_tests.txt —— Wave-1 cohort 5源按价值[gov-cn-policy1.0>...>ndrc-gov0.865]非registry序；每源authority_role/history_start/expected_doc_types/stop_rule/expected_benefit全齐；nda-gov deferred(live blocked)；priority model+manifest+expected benefit，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 按用户价值选A0回填Cohort(高价值中央源优先，每源权威角色/起点/类型/停止规则)
Data/Performance/Visual: Data=Wave-1 cohort manifest；无性能/UI
Value: 十年回填从最有价值处开始，有序可停，受阻源deferred不盲开
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md（Owner cohort门待决，执行T046）
Deployment: NOT_DEPLOYED（cohort提案；Owner cohort门SCALE/HOLD/STOP后进T046）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
