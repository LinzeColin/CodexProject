# TASK_REPORT · ADP-S4-P01-T043｜实现 Source-Year-Month Gap Detector

## 唯一目标（达成）
把**全面性从来源数量变为可见的时间覆盖和缺口**。交付 coverage table、gap reasons、alerts。**每个 enabled source/year/month 有 count 或解释；0 个静默未解释空洞。**

## 六个开始前问题（已回答）
1. **唯一目标**：Source-Year-Month gap detector；每单元有 count 或解释、0 静默空洞、未解释即 alert。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/gap_detector.py, GAP_DETECTOR_SPEC.md}` + 本证据包（coverage_items/coverage_report/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接生产。NOT_DEPLOYED。
4. **基线**：main `7a4e39d7`（T042 三车道已合入）；月域用 T041 分片 2016-01…2026-07。
5. **验收**：每个 enabled source/year/month 有 count 或解释；0 个静默未解释空洞。
6. **回滚**：`git revert <sha>`（纯检测器，生产未变更）。

## 交付物
- `tools/gap_detector.py` —— `build_coverage`（(source,month)→count）+ `classify`（**穷尽缺口原因** covered/source_not_yet_active/no_publications/not_backfilled/fetch_failed/UNEXPLAINED）+ `detect`（网格 + reason 统计 + **alerts**）+ `infer_source_windows` + `month_range`。
- `GAP_DETECTOR_SPEC.md` + `evidence/.../{coverage_items.json, coverage_report.json}`。

## 验收结果（实测，见 test-results/gap_tests.txt，ACCEPTANCE = PASS，exit 0）
真实 500 覆盖：**20 源 × 127 月 = 2540 单元**：
- **每单元有 count 或解释、0 静默空洞**：`covered 75 / not_backfilled 203 / source_not_yet_active 2262`（和=2540），**unexplained=0**，every_cell_has_count_or_reason=True；reason 全为已知类别、计数和=单元数。
- **coverage table**：75 个 covered 单元；交付 coverage table + gap reasons + alerts。
- **alert 有效（不糊弄）**：注入无活跃窗的 `ghost-source` → **127 unexplained → 127 alerts**，证明检测器**会抓静默空洞**而非把一切解释掉。

## Data / Performance / Visual
Data = 2540 单元覆盖网格 + reason 统计 + alerts。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S4 2016+ Expansion）
- **Value**：全面性**可见化**——不再只数「有多少源」，而是每源每月是否有内容、若无则**为什么**（未上线/未回填/确无/抓取失败），**零静默空洞**、未解释即告警；扩 cohort 前能看清覆盖真相。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = detector（真实回填状态校准）。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接生产；backfilled/failed 月集接真实回填后填充）；源活跃窗由已入库条目推断（接真实 enabled_at 校准）；覆盖基于当前抓样；alert 为返回值（推送告警在 T044 看板）；月粒度。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json`、`real_*_smoke` —— N/A。`data-samples` = coverage_items.json + coverage_report.json。

## 完成声明
```text
Task: ADP-S4-P01-T043
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/gap_detector.py + GAP_DETECTOR_SPEC.md + T043 证据包（coverage_items/coverage_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: gap_tests.txt —— 20源×127月=2540单元(covered75/not_backfilled203/source_not_yet_active2262)；unexplained0+每单元count或解释；注入ghost-source→127 unexplained→127 alerts，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Source-Year-Month gap detector（覆盖网格+缺口原因+alerts，0静默空洞）
Data/Performance/Visual: Data=2540单元网格+reason统计+alerts；无性能/UI
Value: 全面性可见化，每源每月有count或原因，未解释即告警
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（检测器，未接生产）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
