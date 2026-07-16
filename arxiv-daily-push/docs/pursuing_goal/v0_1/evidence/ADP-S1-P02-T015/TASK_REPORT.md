# TASK_REPORT · ADP-S1-P02-T015｜加入 Source Drift CI

## 唯一目标（达成）
阻断新手写 source array、UI 标签漂移和 D1 未注册来源 —— 交付 repo scanner、runtime/D1 comparison、approved exception file。

## 六个开始前问题（已回答）
1. 唯一目标：加入 source drift CI，注入第二来源数组/错误标签会失败，正常 build 无误报。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{tools/check_source_drift.py, SOURCE_DRIFT_EXCEPTIONS.yaml}` + 本证据包 + 治理同步。**只读扫描，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED，只读）。
4. 基线：main `826624064`（T014 已合入）；worker REGISTRY 33 源 == compiled/runtime.json 33。
5. 验收：注入第二来源数组或错误标签使 CI 失败；正常 build 无误报。
6. 回滚：`git revert <sha>`（纯工具/文档，NOT_DEPLOYED）。

## 交付物
- `tools/check_source_drift.py` —— repo scanner（worker 只允许 1 个已批准 source array）+ runtime/D1 comparison（worker id 集 == compiled/runtime.json id 集）+ UI 标签漂移（ui_labels.registry_hash == compiled registry_hash）。
- `SOURCE_DRIFT_EXCEPTIONS.yaml` —— approved exception file（当前批准 worker `REGISTRY` 为唯一 source 数组；无未注册来源例外）。

## 验收结果（实测，见 test-results/drift_ci_tests.txt）
- **正常 build 无误报**：真实 worker → `RESULT: PASS`（1 个批准数组 REGISTRY；worker 33 == runtime 33；ui hash 匹配）。
- **注入第二来源数组失败**：加 `REGISTRY2` + 未注册 id `rogue-src` → `RESULT: DRIFT`（同时拦「未批准数组 REGISTRY2」与「未注册来源 rogue-src」，exit 1）。
- **错误标签失败**：篡改 ui_labels.registry_hash → `RESULT: DRIFT`（labels 未从当前 registry 重生成，exit 1）。
- **恢复后**：PASS。

## Data / Performance / Visual
N/A —— 只读扫描，无数据/性能/UI 变更；未碰 worker/D1。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：来源单一事实被 CI 守住 —— 任何新手写 source 数组、未注册的线上来源、或与 registry 不一致的 UI 标签都会让 CI 失败；DRIFT-FACT-006 类漂移不能再悄悄回流。S1-P02（来源单一事实）闭环完成（schema→迁移→编译器→drift CI）。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 行读写 0（扫描仓库文件，未连 D1）；R2 0；模型调用 0；人工维护 = 新增合法来源须注册（改 Registry 重编译）或写入例外文件。经常性云成本 0。

## Known gaps
见 known_gaps.md（scanner 未挂进 GitHub workflow=后续；runtime/D1 比对以 worker REGISTRY 为线上代理，未直连 D1）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI）、`benchmarks`（无性能）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。

## 完成声明
```text
Task: ADP-S1-P02-T015
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: check_source_drift.py + SOURCE_DRIFT_EXCEPTIONS.yaml + 证据 + 治理同步（见 changed_files.txt）
Tests: drift_ci_tests.txt —— 正常 PASS + 注入第二数组/未注册 id DRIFT + 标签 hash 失配 DRIFT + 恢复 PASS；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: source drift CI（repo scanner + runtime/D1 比对 + 标签漂移 + 例外文件）
Data/Performance/Visual: N/A（只读扫描）
Value: 来源单一事实被 CI 守住（S1-P02 闭环：schema→迁移→编译器→drift CI）
Cost: 请求0 / D1 0 / R2 0 / 模型 0 / 人工=新源须注册或写例外；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯工具/文档）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
