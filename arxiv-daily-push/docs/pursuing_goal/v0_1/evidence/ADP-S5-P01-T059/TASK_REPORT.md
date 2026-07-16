# TASK_REPORT · ADP-S5-P01-T059｜建立跨板块 Evidence Relation

## 唯一目标（达成）
连接政策/论文/标准/专利/统计/试点/招采，而不建无边界大图谱。交付 relation types、evidence rules、query examples。**每条关系有文档/片段依据；无证据推断明确标记或不保存。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：跨板块 Evidence Relation——有界词表 + 每条关系有证据 + 无证据推断明确标记/不保存。
2. **允许修改文件**：`tools/evidence_relation.py`（新）+ `evidence/ADP-S5-P01-T059/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——关系层只读。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `2d9f9a13`（T058 已合入）；用真实 backfill 文号作主体。
5. **验收**：每条关系有文档/片段依据；无证据推断明确标记或不保存。
6. **回滚**：`git revert <sha>`（只读关系层，生产未变更）。

## 交付物
- `tools/evidence_relation.py` —— RELATION_TYPES(有界词表) + add_relation(拒 off-vocab/未知 kind;只存有证据;否则 inferred_unsaved) + build_graph + query。
- `evidence/…/relation_report.json` —— 7 断言 → 4 saved/2 refused/1 inferred_unsaved + query examples。
- `evidence/…/build_relations.py`、`evidence/…/test-results/{t059_verify.py, relation_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/relation_tests.txt，ACCEPTANCE = PASS，exit 0）
- **每条关系有文档/片段依据**：7 断言 → **4 saved 全带 {doc_id, fragment(引用片段), source_id}**；every_saved_has_evidence=True；graph 恰含 saved 边(无泄漏)。
- **无证据推断明确标记/不保存**：无证据断言(苏政办函39 supported_by_stat 江苏GDP,无 fragment)→**inferred_unsaved 明确标记,不入图**(既不静默丢也不静默存)。
- **有界非无边界图**：**off-vocabulary((paper)-implements->(policy)) + 未知 board kind(tweet) → refused 不入图**。RELATION_TYPES 固定 8 谓词 + 允许对。
- **query 只返回有证据边**：query(procurement_under)→苏采〔2026〕7号,带证据。
- **负控制**：加无证据关系(P implements Q,无 evidence)→inferred_unsaved,永不入 saved graph。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 7 断言 → 4 saved 边(有证据) + 2 refused + 1 inferred。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**有界、证据化跨板块关系**——政策/论文/标准/统计/试点/招采按固定词表连接,每边有文档/片段依据,无证据推断标记/不存;关系层可信非臆想图。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 关系层编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：有界词表(off-vocab/未知kind拒);只存有证据边(无证据inferred_unsaved);fixture真实文号+现实片段(真实fragment由抽取填);★收尾 S5-P01★。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = relation_report.json。

## 完成声明
```text
Task: ADP-S5-P01-T059
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/evidence_relation.py(新) + T059 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: relation_tests.txt —— 7断言→4 saved全带文档/片段证据;无证据断言→inferred_unsaved标记不入图;off-vocab+未知kind refused(有界非无边界图);query只返回有证据边;负控制(无证据关系永不入saved graph);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 跨板块Evidence Relation(有界词表/每边有证据/无证据标记不存)
Data/Performance/Visual: Data=7断言→4 saved边；Perf=实时无回归；Visual=六主题保留
Value: 有界证据化跨板块关系,关系层可信非臆想
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（关系层；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
