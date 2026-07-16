# TASK_REPORT · ADP-S4-P03-T052｜A1 Coverage/Quality/Cost Gate

## 唯一目标（达成）
决定哪些省市进入持续生产、哪些降频或隔离。交付 A1 scorecard、promote/hold/disable decisions。**官方身份 100%；质量/及时/成本均有实际证据；决定可回滚。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：A1 覆盖/质量/成本 gate——scorecard + 可回滚 promote/hold/disable。
2. **允许修改文件**：`tools/a1_scorecard.py`（新）+ `evidence/ADP-S4-P03-T052/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——gate 只读评分。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `715b714c`（T051 已合入）；读 T050 省级实抓 + T051 城市 cohort 证据。
5. **验收**：官方身份 100%；质量/及时/成本均有实际证据；决定可回滚。
6. **回滚**：`git revert <sha>`；决定绑 feature-flag，不改既有生产数据。

## 交付物
- `tools/a1_scorecard.py` —— 逐 A1 源评分(identity/quality/timeliness/cost) + promote/hold/disable。
- `evidence/…/a1_scorecard.json` —— 22 源 scorecard + 决定 + 可回滚声明。
- `evidence/…/build_scorecard.py`、`evidence/…/test-results/{t052_verify.py, scorecard_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/scorecard_tests.txt，ACCEPTANCE = PASS，exit 0）
- **官方身份 100%**：22 源全验证 A1（official_identity_rate=1.0）——省级经 T050 verify 赢得 A1、城市经 T051 身份核验 A1。
- **质量/及时/成本实际证据**：**3 promote**=江苏/山东/北京（各 3 内容寻址 A1 文档 + 真实日期 + 月份[2026-06/07]，真实质量/及时证据）；**18 hold**=城市（验证 A1 但 original_fetch pending，docs=0 诚实非 UNKNOWN 冒充）；**1 disable**=广东（T050 隔离/被挡，0 文档）。成本=dev-env 0 云；未测标 UNKNOWN 不填 0。
- **决定可回滚**：NOT_DEPLOYED；决定=recommendation 绑 feature-flag；不改既有生产数据；回滚=git revert/flag off；每行 reversible=True。
- **负控制（晋级需赢得非给予）**：①18 城市验证 A1+明确价值但**无 promote**（不凭价值晋级，因无实抓原文→hold）②广东被挡→**disable 非 promote**③promote 全有 docs≥1+内容寻址+日期证据。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 22 源 scorecard（3 promote/18 hold/1 disable）+ 决定证据。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A1 Expansion）
- **Value**：**A1 证据化门控晋级决定**——只在实证质量/及时上 promote，未验证 hold，故障 disable；不为覆盖数字晋级；决定可回滚。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = scorecard 编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：决定基于当前 SHADOW 证据；及时窗口小（各省 3 文档）；城市 hold 待 headless+T053；成本 dev-env 0 云；A2 是 T053-T055。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED）。`data-samples` = a1_scorecard.json。

## 完成声明
```text
Task: ADP-S4-P03-T052
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/a1_scorecard.py(新) + T052 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: scorecard_tests.txt —— 22源官方身份100%；质量/及时/成本实证(3 promote有真文档/18 hold诚实0/1 disable真故障)；决定可回滚(NOT_DEPLOYED+flag)；负控制(城市不凭价值晋级/广东disable);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A1证据化门控(3 promote/18 hold/1 disable,身份100%,可回滚)
Data/Performance/Visual: Data=22源scorecard；Perf=实时无回归；Visual=六主题保留
Value: A1证据化晋级决定,不为覆盖数字晋级
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（scorecard；生产未触，实时无回归）
Rollback: git revert <sha> / feature-flag off
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
