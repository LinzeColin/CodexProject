# TASK_REPORT · ADP-S5-P01-T058｜实现跨来源实体解析

## 唯一目标（达成）
统一机关、机构、作者、公司、地区、主题和标准等实体。交付 entity schema、aliases、provenance、merge/split audit。**错误合并可撤销；实体来源和置信边界可追溯。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：跨来源实体解析——统一实体,错误合并可撤销,provenance/置信边界可追溯。
2. **允许修改文件**：`tools/entity_resolver.py`（新）+ `evidence/ADP-S5-P01-T058/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——resolver 只读。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `407bd1e1`（T057 已合入）；用真实机关别名。
5. **验收**：错误合并可撤销；实体来源和置信边界可追溯。
6. **回滚**：`git revert <sha>`（只读 resolver，生产未变更）。

## 交付物
- `tools/entity_resolver.py` —— entity schema + resolve(共享 alias 聚类 + 逐源 provenance) + merge(deepcopy before 快照 + audit + 置信边界) + split(逐字节反向) + provenance_of。
- `evidence/…/entity_report.json` —— 7 mentions → 4 实体 + merge/split audit + 置信边界。
- `evidence/…/build_entities.py`、`evidence/…/test-results/{t058_verify.py, entity_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/entity_tests.txt，ACCEPTANCE = PASS，exit 0）
- **跨来源统一**：7 mentions → 4 实体;国家统计局≡统计局≡NBS(NBS 来自 media-x 独立 mention 并入)、国务院办公厅≡国办、发改委≡NDRC。**无共享 alias 的不同机关保持独立**(防误并)。
- **错误合并可撤销（精确）**：故意误并(国家统计局+国务院办公厅,高置信)→2 实体;split→3 实体,**逐字节还原**(restored[a]==原 and restored[b]==原,len 一致)。
- **provenance 可追溯**：每 alias 记 source_id;provenance_of 覆盖全 aliases 无 unsourced;多源别名可溯来源边界。
- **置信边界**：AUTO_MERGE_MIN=0.80;低置信(0.5)合并→**pending_review 不应用**(实体不变);高置信(0.95)→applied。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 7 mentions → 4 实体 + merge/split audit。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S5 多板块深度）
- **Value**：**可撤销、有源、置信有界的实体解析**——同机关跨板块归一,误并可撤,弱信号不静默过并,每别名可溯源;实体层可信。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = resolver 编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：合并靠共享 alias(无模糊);可撤销靠 deepcopy 快照;置信边界 0.80;alias 集为 curated 示例(真实随抓取积累);跨板块 relation T059。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = entity_report.json。

## 完成声明
```text
Task: ADP-S5-P01-T058
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/entity_resolver.py(新) + T058 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: entity_tests.txt —— 7 mentions→4实体跨源统一(NBS并入国家统计局);错误合并可撤销(merge→split逐字节还原);provenance逐alias有源;置信边界(低置信0.5→pending_review不应用/高置信0.95→applied);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 跨来源实体解析(可撤销/有源/置信有界)
Data/Performance/Visual: Data=7 mentions→4实体+audit；Perf=实时无回归；Visual=六主题保留
Value: 可撤销有源置信有界的实体解析,实体层可信
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（resolver库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
