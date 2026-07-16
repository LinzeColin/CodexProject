# TASK_REPORT · ADP-S1-P03-T017｜建立当前 200 样本内容缺陷基线

## 唯一目标（达成）
量化英文直出、重复、模板、无证据、空栏目和板块污染 —— 交付 baseline dataset、defect labels、before report。

## 六个开始前问题（已回答）
1. 唯一目标：对 200 真实样本机器打标 6 类内容缺陷，每条可回 item_id/document_id/build_id，量化 before 报告。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{tools/scan_defects.py, defect_baseline_200.json}` + 本证据包 + 治理同步。**复用 T016 的 200 样本与 factsheet，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED，只读）。
4. 基线：main `d0a5beef`（T016 已合入）；样本 = T016 的 200 条 cn_items + factsheet_baseline_200.json；build_id `bd67a78020a3`。
5. 验收：每条缺陷可回 item_id/document_id/build_id；不以主观描述代替样本。
6. 回滚：`git revert <sha>`（纯工具/数据，NOT_DEPLOYED）。

## Owner 决策
按 Owner 2026-07-16 指令，缺陷基线为**机器基准 `provisional_machine`**（待 Owner 抽查），不捧造人工标签。

## 交付物
- `tools/scan_defects.py` —— 确定性缺陷扫描器（6 类：english_direct_output/duplication/templating/no_evidence/empty_section/board_pollution）。
- `defect_baseline_200.json` —— baseline dataset（200 行，每行 item_id/document_id/build_id/board/defects）+ before_report（量化计数）。

## 验收结果（实测，见 test-results/defect_tests.txt）
- **before report（量化，非主观）**：english_direct_output **113/200**（证实 FACT-002 英文直出）、board_pollution **44/200**（证实 FACT-003 板块污染，主要 board3 非政策）、templating 6、empty_section 1、no_evidence 0；**160/200 至少一处缺陷**。
- **每条缺陷可回 item_id/document_id/build_id**：200 行全部含 item_id+document_id+build_id=`bd67a78020a3`（True）；示例可见具体 item_id + 标签（不以主观描述代替样本）。
- **确定性**：重扫字节一致（True）。

## Data / Performance / Visual
- Data：复用 T016 只读样本（未新连 D1，0 新 D1 读）；产出 200 行缺陷标签。
- Performance/Visual：N/A。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：把内容缺陷从主观「感觉英文太多」变成**可回溯量化基线**——113/200 英文直出、44/200 板块污染，每条挂到 item_id 与当前 build，成为 T018 人话版改造的 before 对照与验收锚。
- **Cost（逐项，未知不填 0）**：新增请求 0（复用 T016 样本）；D1 读写 0；R2 0；模型调用 0；人工维护 = Owner 抽查 provisional 标签（后续）。经常性云成本 0。

## Known gaps
见 known_gaps.md（缺陷判据为启发式 provisional；样本为近 200 条；duplication 仅 batch 内）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI）、`benchmarks`（before 报告即 before.json 等价，附于 baseline）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`data-samples`=defect_baseline_200.json。

## 完成声明
```text
Task: ADP-S1-P03-T017
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: scan_defects.py + defect_baseline_200.json + 证据 + 治理同步（见 changed_files.txt）
Tests: defect_tests.txt —— 200 行全含 item/document/build_id True + 确定性 True + before 报告量化；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: before report（英文直出 113/200、板块污染 44/200、160/200 有缺陷），每条可回 item_id/build_id
Data/Performance/Visual: 复用 T016 样本（0 新 D1 读）
Value: 内容缺陷可回溯量化基线（T018 before 锚；证实 FACT-002/003）
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md（provisional 待 Owner 抽查）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯工具/数据）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
