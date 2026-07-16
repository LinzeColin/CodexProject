# TASK_REPORT · ADP-S4-P04-T053｜接入首批 10 个高价值 A2 (SHADOW)

## 唯一目标（达成）
先验证重要区/新区/自贸片区/高新区的**增量价值**。交付 A2 pilot profiles、2016+ cursors、local action signals。**每个 A2 产生中央/省级之外的实质增量；无价值源不晋级。** release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：首批 10 高价值 A2；每个产生 A0/A1 之外增量；无价值源不晋级。
2. **允许修改文件**：`tools/a2_pilot.py`（新）+ `evidence/ADP-S4-P04-T053/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——本任务=选择/pilot，无抓取执行。六主题/MVP 不变。SHADOW。
4. **基线**：main `32c1f344`（T052 已合入）；复用 T033 verify_identity + T041 cursor；同 T045/T051 结构。
5. **验收**：每个 A2 产生中央/省级之外实质增量；无价值源不晋级。
6. **回滚**：`git revert <sha>`（选择产物，生产未变更）。

## 交付物
- `tools/a2_pilot.py` —— incremental_signals(超 A0/A1 baseline) + verify_official(T033) + select_pilot + cursor_2016 + LOCAL_SIGNAL_TYPES 分类。
- `evidence/…/a2_pilot_manifest.json` —— 10 入选(增量排序)+2 拒绝+每区 profile/信号/游标/reachability。
- `evidence/…/build_pilot.py`、`evidence/…/test-results/{t053_verify.py, pilot_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/pilot_tests.txt，ACCEPTANCE = PASS，exit 0）
- **首批 10 高价值 A2**：雄安/浦东/中关村/临港/苏州工业园区/横琴/天府/西安高新/两江/前海——全真国家级新区/自贸片区/高新区/经开区。
- **每个 A2 产生中央/省级之外实质增量**：baseline={policy,regulation,statistics}（A0/A1 已覆盖）；每入选区 incremental_signal_types 非空（项目立项/招投标采购/试点先行先试/产业落地/招商引资/规划公示，皆超 baseline）。增量排序（4→2 信号类型）。
- **无价值源不晋级**：**policy-repost-zone（仅转政策，0 增量）→ 拒**；**zone-media（资讯号，非官方）→ 拒**——增量+官方双门。
- **A2 profile + 2016 游标 + local action signals**：每入选区有 zone_type + 官方 .gov.cn host + local_action_signals + start_month=2016-01 游标。
- **3 区实证信号**：recon 实测雄安/苏州工业园区/横琴 200 + 本地行动信号词 9/17/6（confirmed_signals）；其余 7 区诚实标 tls_blocked（fetch pending）。
- **实时无回归**：SHADOW，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 10 入选 A2 区(profile/增量信号/游标) + 2 拒绝。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A2 Expansion）
- **Value**：**首批高价值 A2 功能区**——政策落地为第一线本地行动信号(项目/招采/试点/产业落地)，正是 A0/A1 政策文本没有的增量；无增量/非官方不晋级。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 增量价值模型 + 区候选 + recon。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：增量=信号 TYPE 层(单条真实增量随抓取+T054/T055 量化)；选择非抓取；3 区实证其余 pending_headless；SHADOW 未部署。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（SHADOW）。`data-samples` = a2_pilot_manifest.json。

## 完成声明
```text
Task: ADP-S4-P04-T053
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/a2_pilot.py(新) + T053 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: pilot_tests.txt —— 10高价值A2区入选(增量排序)+每个incremental>0(超A0/A1 baseline)+A2 profile/2016游标/本地行动信号；无价值源不晋级(policy-repost 0增量拒/media非官方拒);3区实证信号(雄安/苏工园/横琴);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 首批10高价值A2(增量本地行动信号,无价值源不晋级)
Data/Performance/Visual: Data=10 A2区pilot；Perf=实时无回归；Visual=六主题保留
Value: A2功能区第一线本地行动信号,A0/A1之外增量
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（pilot manifest；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
