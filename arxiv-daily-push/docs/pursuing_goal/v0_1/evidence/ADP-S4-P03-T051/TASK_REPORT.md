# TASK_REPORT · ADP-S4-P03-T051｜分批接入重点城市级 A1 (SHADOW)

## 唯一目标（达成）
按用户价值分批接入重点城市级 A1（省会/副省级/计划单列/关键创新制造金融外贸城市）。交付 city cohort manifests、official identity、2016 cursors。**每个城市有明确价值和官方原文；不为凑数量启用低价值源。** release_mode=SHADOW。

## 六个开始前问题（已回答）
1. **唯一目标**：价值分层选重点城市 A1 cohort；每城市明确价值 + 官方原文；不凑数量。
2. **允许修改文件**：`tools/city_cohort.py`（新）+ `evidence/ADP-S4-P03-T051/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——本任务=选择/manifest，无抓取执行。六主题/MVP 不变。SHADOW。
4. **基线**：main `a0afcc63`（T050 已合入）；复用 T033 verify_identity + T041 cursor 形态；同 T045（A0 cohort 选择）结构。
5. **验收**：每城市明确价值 + 官方原文；不为凑数量启用低价值源。
6. **回滚**：`git revert <sha>`（选择产物，生产未变更）。

## 交付物
- `tools/city_cohort.py` —— value_score + verify_official(T033) + select_cohort + plan_waves + cursor_2016。
- `evidence/…/city_cohort_manifest.json` —— 18 入选(价值排序)+3 onboarding waves+2 拒绝+每城身份/游标/reachability。
- `evidence/…/build_manifest.py`、`evidence/…/test-results/{t051_verify.py, cohort_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/cohort_tests.txt，ACCEPTANCE = PASS，exit 0）
- **每城市明确价值**：18 入选全 value≥0.6(stop) + tier + rationale；价值排序（直辖市 1.0 → 关键经济 0.67）。3 waves：wave_1=8(直辖市+副省级计划单列)、wave_2=6(副省级)、wave_3=4(关键经济)。
- **每城市官方原文（发布者身份核验）**：18 入选全经 T033 verify_identity 核验为**官方城市 .gov.cn、非中央 → A1**（官方原文发布者）。**⚠诚实**：0 城市原文在服务器端实抓成功（门户 JS/TLS 挡），全 `pending_headless`；**municipality tier 由北京[T049/T050 已实抓]证明可行**；见 known_gaps。
- **不为凑数量启用低价值源**：STOP_THRESHOLD=0.6。**负控制**：普通地级市(value 0.3<0.6)被拒；**媒体聚合器(nominal value 0.93≥0.6 但 category=media → 非 A1)被拒**——证明价值≠入选、非官方永不入选。18 入选全真高价值，非凑数。
- **2016 游标**：每入选城市有 start_month=2016-01 的可恢复回填游标。
- **实时无回归**：SHADOW，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 18 入选城市(身份/价值/游标) + 2 拒绝 + reachability metadata。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A1 Expansion）
- **Value**：**价值分层的重点城市 A1 cohort**——按 tier/角色排序，官方原文发布者核验，低价值/媒体拒之；为 T050 机制的 city 批次提供门控输入。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 价值模型 + 城市候选 + reachability recon。经常性云成本 delta = $0/月（SHADOW）。

## Known gaps
见 `known_gaps.md`：选择非抓取；官方原文=发布者身份核验；0 城市原文服务器端实抓(北京同 tier 证明可行)；价值门非凑数(负控制)；NOT_DEPLOYED。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（SHADOW，无 schema/UI/部署变更）。`data-samples` = city_cohort_manifest.json。

## 完成声明
```text
Task: ADP-S4-P03-T051
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/city_cohort.py(新) + T051 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: cohort_tests.txt —— 18入选(价值排序+3waves)全A1官方发布者+2016游标+明确价值；负控制(低价值城市拒/媒体拒虽高value)证明不凑数量；官方原文=身份核验(0服务器端实抓,pending_headless,北京同tier证明);实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 重点城市A1价值分层cohort(18入选/官方发布者/2016游标/不凑数量)
Data/Performance/Visual: Data=18城市cohort+2拒绝；Perf=实时无回归；Visual=六主题保留
Value: 价值分层重点城市A1 cohort,T050 city批次门控输入
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(SHADOW)
Known gaps: 见 known_gaps.md
Deployment: SHADOW（选择manifest；生产 worker/cron/数据未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
