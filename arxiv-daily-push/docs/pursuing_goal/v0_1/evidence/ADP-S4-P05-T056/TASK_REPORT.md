# TASK_REPORT · ADP-S4-P05-T056｜Coverage Debt 与 As-of 历史查询底座

## 唯一目标（达成）
展示 2016+ 哪些地域/年份/类型完整，并支持截至某日恢复当时已知版本。交付 coverage API、as-of query、historical manifest resolver。**100 个修订样本查询不同日期不使用未来版本；覆盖空洞可解释。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：Coverage Debt + As-of 历史查询底座——覆盖完整度可解释 + as-of 无未来泄漏。
2. **允许修改文件**：`tools/coverage_asof.py`（新）+ `evidence/ADP-S4-P05-T056/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——底座只读查询。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `03a65a16`（T055 已合入）；复用 T043 gap detector + T048 as-of resolver；读 A0(T046/T047)+A1(T050)语料。
5. **验收**：100 修订样本查不同日期不用未来版本；覆盖空洞可解释。
6. **回滚**：`git revert <sha>`（只读底座，生产未变更）。

## 交付物
- `tools/coverage_asof.py` —— coverage_debt + as_of_query(+独立 oracle) + build_revision_chains + asof_samples + historical_manifest_resolver。
- `evidence/…/coverage_asof_report.json` —— coverage 网格 + debt + as-of 样本 + 点时 manifest 解析。
- `evidence/…/build_base.py`、`evidence/…/test-results/{t056_verify.py, base_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/base_tests.txt，ACCEPTANCE = PASS，exit 0）
- **100+ 修订样本不用未来版本**：**693 as-of 样本**（21 链 × 33 查询日 2016–2026）**未来版本泄漏 0** + 与独立 oracle **0 分歧**；用解析日期(y,m,d)非字符串。
- **覆盖空洞可解释**：coverage 网格 = 5 源 × 2016+ 窗口全月 = **180 格**；covered 11 / **debt 169**（source_not_yet_active 139 + not_backfilled 30）；**unexplained=0，every_hole_explained=True**。
- **非空洞控制（as-of 真判别）**：顺序 spot-check（查询早于 v1→无；v1→v1；v2→v2；远未来→v2）正确；**故意 broken resolver 在版本间查询确产生未来解析（被抓）**；**畸形日期被拒**。
- **historical manifest resolver 永不未来**：as-of 2015→None、2020-06→2019-12、2099→2026-07（≤查询日的最新 manifest）。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 180 格 coverage 网格(169 debt/0 unexplained) + 693 as-of 样本 + 点时 manifest。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 Coverage Debt 与 As-of）
- **Value**：**地面完整度 + 点时历史查询底座**——诚实答「此处 2016+ 是否完整」「截至某日已知什么版本」不泄漏未来;T048 gap gate 推迟的地面真值层。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 底座编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：底座建于当前语料;as-of 非同义反复(oracle+broken/malformed 控制);「完整」是回填口径(源发布真值仍需权威日历,承 T048);manifest=月度快照点时;NOT_DEPLOYED。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = coverage_asof_report.json。

## 完成声明
```text
Task: ADP-S4-P05-T056
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/coverage_asof.py(新) + T056 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: base_tests.txt —— 693 as-of样本0未来泄漏/0 oracle分歧(≥100修订样本);coverage 180格0未解释(169 debt全可解释);非空洞控制(broken resolver泄漏被抓/畸形日期拒/顺序对);manifest永不未来;实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Coverage Debt+As-of底座(693样本0泄漏,169 debt全可解释,点时manifest)
Data/Performance/Visual: Data=180格coverage+693 as-of样本；Perf=实时无回归；Visual=六主题保留
Value: 地面完整度+点时历史查询底座,不泄漏未来
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（查询底座；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
