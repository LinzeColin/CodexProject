# TASK_REPORT · ADP-S1-P02-T014｜实现 Registry 编译器与确定性输出

## 唯一目标（达成）
由一个源生成 runtime、UI labels、D1 seed、health 和 backfill plan —— 交付 compiler、validator、runtime JSON、UI JSON、seed SQL、registry hash。

## 六个开始前问题（已回答）
1. 唯一目标：实现从单一 source_registry.json 确定性编译出 runtime/UI/seed/hash 的编译器，并在非法输入时失败。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{tools/compile_registry.py, compiled/*}` + 本证据包 + 治理同步。**不改 worker/D1/生产**（编译产物不应用）。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED，seed 不应用）。
4. 基线：main `0b0e9422`（T013 已合入）；输入 = source_registry.json（33 源，T013 迁入）。
5. 验收：连续两次编译字节一致；duplicate ID、非法 enabled、未知 authority 均失败。
6. 回滚：`git revert <sha>`；seed 未应用于生产（rollback.sql 记录：无生产回滚需求）。

## 交付物
- `tools/compile_registry.py` —— 编译器：先跑 T012 validator + 硬检查（duplicate id / 非布尔 enabled / 未知 authority），再确定性输出。
- `compiled/runtime.json` —— worker 运行时源（按 source_id 排序，含 registry_hash）。
- `compiled/ui_labels.json` —— UI 标签 + official/discovery 徽章。
- `compiled/seed.sql` —— D1 cn_sources 确定性 INSERT（按 source_id 排序）。
- `compiled/registry_hash.txt` —— `sha256:d63cf6bd…`。

## 验收结果（实测，见 test-results/compile_tests.txt）
- **连续两次编译字节一致**：两次编译 source_registry.json，四个输出目录哈希相同（byte-identical True）；registry_hash `sha256:d63cf6bd4d72…e7fb`（无时间戳、排序键，故确定）。
- **duplicate ID 失败**：重复 source_id → COMPILE: FAIL（exit 1）。
- **非法 enabled 失败**：enabled="yes"（非布尔）→ FAIL（schema + 硬检查）。
- **未知 authority 失败**：authority_kind="propaganda" → FAIL（schema enum + 硬检查）。

## Data / Performance / Visual
- Data：从 33 源确定性产出 runtime(33)/UI(33)/seed(33 INSERT)；未写 D1（seed 未应用）。
- Performance/Visual：N/A（未碰运行时/UI）。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：runtime/UI/seed 由**一个 Registry** 确定性生成 —— 消除多份来源真相的机制到位（T013 登记，T014 生成机制）；registry_hash 让来源集可 hash 比对（为 T015 drift CI 供锚）。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 行读写 0（seed 未应用）；R2 0；模型调用 0；人工维护 = 改 Registry 后重跑编译器（可 CI 化）。经常性云成本 0。

## Known gaps
见 known_gaps.md（health/backfill 为占位；seed 未应用；worker 尚未改为读 compiled/runtime.json=后续部署任务）。

## 不适用证据项
`benchmarks`（无性能）、`screenshots-or-videos`（无 UI）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`migration.sql`=compiled/seed.sql（附 rollback.sql）；`data-samples`=compiled/*。

## 完成声明
```text
Task: ADP-S1-P02-T014
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: compile_registry.py + compiled/{runtime.json,ui_labels.json,seed.sql,registry_hash.txt} + 证据 + 治理同步（见 changed_files.txt）
Tests: compile_tests.txt —— 两次编译字节一致 True + 3 负例(dup id/非布尔 enabled/未知 authority)全 FAIL；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 由一个 Registry 确定性生成 runtime/UI/seed，registry_hash sha256:d63cf6bd…
Data/Performance/Visual: 33 源确定性产出（未写 D1）
Value: 单一 Registry 确定性生成 runtime/UI/seed（消除多份真相机制）
Cost: 请求0 / D1 0 / R2 0 / 模型 0 / 人工=改 Registry 重跑编译；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（seed 未应用于生产，见 rollback.sql）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
