# TASK_REPORT · ADP-S4-P01-T042｜建立 Realtime/Catchup/Backfill 三车道与自动暂停

## 唯一目标（达成）
建立**三车道**（realtime/catchup/backfill）+ **自动暂停**，保证历史回填**永远不能拖垮当前第一线数据**。交付 priority rules、queue quotas、backpressure、kill switch。**压力测试时 realtime freshness P95 ≤ 基线+20%；超阈值自动暂停 backfill。**

## 六个开始前问题（已回答）
1. **唯一目标**：三车道调度 + 背压自动暂停；realtime P95 ≤基线+20%、超阈值暂停 backfill。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/three_lane_scheduler.py, THREE_LANE_SPEC.md}` + 本证据包（stress_test_report/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接生产。NOT_DEPLOYED。
4. **基线**：main `20c94431`（T041 planner 已合入）；与 T041 backfill planner 联动。
5. **验收**：压力测试时 realtime freshness P95 ≤基线+20%；超阈值自动暂停 backfill。
6. **回滚**：`git revert <sha>`（纯调度逻辑，生产未变更）。

## 交付物
- `tools/three_lane_scheduler.py` —— `schedule`（**优先级** realtime>catchup>backfill + **配额** BASE_QUOTA + **背压** 投影 realtime P95>基线×1.2 则逐步撤 backfill/节流 catchup + **kill switch**）+ `project_p95` + `stress_test`；`Decision{alloc, realtime_p95, within_ceiling, backfill_paused, catchup_throttled, reason}`。
- `THREE_LANE_SPEC.md` + `evidence/.../stress_test_report.json`。

## 验收结果（实测，见 test-results/scheduler_tests.txt，ACCEPTANCE = PASS，exit 0）
压力测试 baseline=10、capacity=20、天花板=12（+20%）：
- **不变量：每个场景 realtime freshness P95 ≤ 基线+20%**（healthy 11.9 / pressure 11.8 / burst 11.6 / kill 10.8，全 ≤12），且 realtime **总被完整服务**（不被下位车道饿死）。
- **超阈值自动暂停 backfill**：**heavy_realtime_burst → backfill 6→0 自动暂停**（bf_paused=True）；backfill 授予随 realtime 压力上升**单调不增 [3,2,0]**（healthy 跑满 3 → pressure 节流 2 → burst 暂停 0）。
- **kill switch**：backfill 5→0 立即暂停。
- **priority + quotas + backpressure + kill switch** 齐备。

## Data / Performance / Visual
Data = 4 压力场景调度结果。Performance = 背压模型守住 realtime P95 ≤基线+20%。无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S4 2016+ Expansion）
- **Value**：三车道 + 背压使 **realtime 第一线数据永不被历史回填拖垮**——realtime P95 在任何负载下守住 +20% 天花板，realtime 突发时 backfill **自动暂停**，kill switch 可强制停；十年回填与实时新鲜度和平共存。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 调度器 + 背压模型（真实基线校准）。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接生产 cron）；freshness 为结构性背压模型（真实 P95 待真实负载校准）；capacity/quota 抽象单元（真实映射 Worker 子请求/DIR-007）；kill switch 为参数；catchup 车道待细化。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`（用 stress_test）、`deployment_manifest.preview.json`、`real_*_smoke` —— N/A。`data-samples` = stress_test_report.json。

## 完成声明
```text
Task: ADP-S4-P01-T042
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/three_lane_scheduler.py + THREE_LANE_SPEC.md + T042 证据包（stress_test_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: scheduler_tests.txt —— realtime P95≤基线+20%全场景(11.9/11.8/11.6/10.8≤12)+realtime总满足；heavy burst backfill 6→0自动暂停+授予单调[3,2,0]+kill switch 5→0；priority+quotas+backpressure+kill switch，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 三车道(realtime/catchup/backfill)+背压自动暂停(历史回填不拖垮第一线)
Data/Performance/Visual: Data=4压力场景；Perf=realtime P95守+20%；无UI
Value: realtime第一线永不被回填拖垮，突发自动暂停backfill，kill switch可强停
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（调度逻辑，未接生产 cron）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
