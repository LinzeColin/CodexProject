# TASK_REPORT · ADP-S5-P04-T067｜实现 Library、笔记和 Provenance 导出

## 唯一目标（达成）
让阅读与证据成为**长期资产**而非只存在 Today：用户把条目存入 **Library**（含笔记/collection），并导出 **Markdown/CSV/JSON**。**每条导出都携带完整 Provenance**——原始 URL、版本、抓取时间、claim evidence 与许可提示——导出自描述、绝不脱证据复制。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：save/note/collection Library + MD/CSV/JSON 导出，**每条含 5 项 provenance**（URL/版本/抓取时间/证据/许可）。
2. **允许修改文件**：`tools/library_export.py`（新）+ `evidence/ADP-S5-P04-T067/*` + 治理同步。**不改 worker/生产/registry/VERSION**。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、无时钟（抓取时间来自条目）。
4. **基线**：main `10d464ff`（T066 已合入）；Golden Library（含中英、笔记、collection、format-hostile 字符条目）。
5. **验收**：三格式每条含 5 项 provenance（含许可提示）；缺 provenance 拒存/拒导出（负控制）；CSV/MD 逐条完整、特殊字符无损。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/library_export.py` —— `new_library/add_to_library`（存条目并强制 provenance 完整，缺则 **raise 拒存**）+ `provenance_complete`（5 项非空，None/[]/空白串=缺，0 等真值算有）+ `export_markdown/export_csv/export_json`（各含全部 provenance；`_assert_exportable` 缺则 **raise 拒导**）+ `export(lib,fmt)`。
- `evidence/…/build_library_export.py`（3 条 Golden：arXiv/中国政策/format-hostile 逗号引号换行；1 条缺 provenance 负样本）+ `library_export_report.json` + `export_sample.{md,csv,json}` + `test-results/{t067_verify.py, library_export_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/library_export_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 三格式每条含全 provenance**：JSON **逐条** provenance 5 项非空；CSV **逐行**每 provenance 列非空；Markdown **逐条 block**（单条重导校验，非全串子串）含全 5 标签+值。3 条目全过。
- **② 许可提示**：markdown/csv/json **每格式每条**均含 license 文本。
- **③ CSV 完整性**：含**逗号/引号/换行**的值经 `csv.DictReader` **无损 round-trip**（DictWriter 正确引用）。
- **④ JSON round-trip**：导出再解析 provenance 完全一致。
- **⑤ 缺 provenance 拒绝（负控制/判别力）**：缺 license+claim_evidence 的条目 **add 时 raise 拒存**；即便构造空 license 混入，**三格式导出全 raise 拒导**；`provenance_complete` 对空 license 返回 False（非空跑）。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 3 条 Golden Library（中英 + format-hostile）+ 3 导出样本。Performance = 实时无回归。无 UI 改动；六主题保留（导出为库层，供 Library/导出视图消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**证据化长期资产**——阅读/证据可存入 Library、加笔记/归集、导出 MD/CSV/JSON，**每条自带原始 URL/版本/抓取时间/证据/许可**；不脱证据、可长期引用、可迁出，缺 provenance 直接拒绝（可信资产而非裸复制）。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 导出器 + Golden + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：provenance 5 项由条目携带（上游摄取提供 URL/版本/抓取时间/证据/许可）；许可提示为文本字段（真实许可判定/合规由法务与源注册表提供）；导出为库层字符串（文件落盘/下载由部署阶段视图负责）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = export_sample.{md,csv,json} + report。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S5-P04-T067
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/library_export.py(新) + T067 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: library_export_tests.txt —— JSON逐条+CSV逐行+MD逐条block全含5项provenance;许可提示三格式每条;CSV逗号引号换行无损round-trip;JSON round-trip一致;缺provenance拒存+拒导(三格式)判别;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Library save/note/collection + MD/CSV/JSON导出(每条含URL/版本/抓取时间/证据/许可)
Data/Performance/Visual: Data=3 Golden Library(中英+特殊字符)；Perf=实时无回归；Visual=六主题保留
Value: 证据化长期资产,每条自带完整provenance,缺则拒绝,可迁出可引用
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
