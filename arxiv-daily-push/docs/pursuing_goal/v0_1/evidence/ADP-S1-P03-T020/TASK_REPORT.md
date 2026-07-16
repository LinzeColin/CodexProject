# TASK_REPORT · ADP-S1-P03-T020｜建立 500 条 Golden Set 与内容 Release Gate

## 唯一目标（达成）
将内容质量变成持续可验收的发布门 —— 交付 500 sample index、human rubric、CI gate、before/after report。

## 六个开始前问题（已回答）
1. 唯一目标：建 500 Golden Set + 人工 rubric + 内容 Release Gate（CI），把内容质量变成可验收门。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{tools/content_release_gate.py, golden_set_500.json, GOLDEN_SET_RUBRIC.md}` + 本证据包 + 治理同步。**只读 D1 抽 500，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED，只读）。
4. 基线：main `18484c4a`（T019 已合入）；样本 = 500 条 cn_items（read-only，changed_db=False）；build_id `bd67a78020a3`。
5. 验收：关键声明证据 100%；空章节/模板泄漏 0；P0 事实准确率 ≥99%；失败只阻断内容 bundle。
6. 回滚：`git revert <sha>`（纯工具/数据，NOT_DEPLOYED）。

## Owner 决策
human rubric 与 P0 准确率按 Owner 2026-07-16 指令**暂用 provisional_machine**（Release Gate 机器判据 + rubric 待人工抽查），不捧造人工标签。

## 交付物
- `golden_set_500.json` —— 500 sample index（item_id/board/source/P0 字段，provisional）。
- `GOLDEN_SET_RUBRIC.md` —— human rubric（P0 事实/关键声明证据/空·模板/语言/事实-解释-推断 + 评分流程）。
- `tools/content_release_gate.py` —— CI gate：key evidence 100% / 空·模板 0 / P0 fidelity ≥ 阈值；失败 scope=content_bundle。
- `BEFORE_AFTER.md` + `benchmarks/{before,after}.json` —— before/after report。

## 验收结果（实测，见 test-results/release_gate.txt）
- **关键声明证据 100%**：500 payload key_unlocated=**0** → key_claim_evidence_100 通过。
- **空章节/模板泄漏 0**：empty_or_template=**0** → 通过。
- **P0 事实准确率 ≥99%**：p0_fact_accuracy=**1.0**（机器保真；provisional 待人工）→ 通过（阈值 0.99）。
- **失败只阻断内容 bundle**：注入空 L0 + 未定位 key fact → **BLOCK_CONTENT_BUNDLE**（scope=content_bundle，exit 1），不涉及部署。
- **before/after**：BEFORE 460/500 缺陷（english_direct_output 361）→ AFTER RELEASE（0 泄漏 + 100% 定位）。

## Data / Performance / Visual
- Data：只读抽 500（0 写）；产出 golden set + before/after。
- Performance/Visual：N/A。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：内容质量变成**持续可验收发布门**——500 Golden Set + Release Gate（key evidence 100% / 空·模板 0 / P0 保真）+ rubric；before 460/500 缺陷在契约层收敛为 RELEASE；失败只挡内容 bundle 不挡部署。**S1-P03 完成**（factsheet→缺陷基线→L0-L3人话版→QA回退→Golden Set/Release Gate）。
- **Cost（逐项，未知不填 0）**：新增请求 = 1 次只读 D1 SELECT（500 行）；D1 rows_read ≈ 500；D1 写 0；R2 0；模型调用 0；人工维护 = Owner 按 rubric 抽查 ≥50 条升 human_verified。经常性云成本 0。

## Known gaps
见 known_gaps.md（P0 准确率为机器保真 provisional 待人工；Gate 未挂 GitHub workflow；board1 样本此窗口 217 条）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（未接渲染）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`data-samples`=golden_set_500.json；`benchmarks`=before/after。

## 完成声明
```text
Task: ADP-S1-P03-T020
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: content_release_gate.py + golden_set_500.json + GOLDEN_SET_RUBRIC.md + BEFORE_AFTER.md + 证据 + 治理同步（见 changed_files.txt）
Tests: release_gate.txt —— AFTER 500 RELEASE(key evidence 100%/空·模板0/P0 1.0)+负测 BLOCK_CONTENT_BUNDLE；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 500 Golden Set + Release Gate + rubric；before 460/500 缺陷→after RELEASE
Data/Performance/Visual: 只读抽 500（0 写）；before/after report
Value: 内容质量持续可验收发布门（S1-P03 完成）
Cost: 1 只读 D1 SELECT / rows_read≈500 / 写0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md（P0 准确率 provisional 待人工）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯工具/数据）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
