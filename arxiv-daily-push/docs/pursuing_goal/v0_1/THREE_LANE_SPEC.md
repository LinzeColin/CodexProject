# Three-Lane Scheduler + Auto-Pause Spec · ADP-S4-P01-T042

**Realtime / Catchup / Backfill 三车道** + 背压自动暂停：保证 2016+ 历史回填**永远不能拖垮当前第一线数据**。
工具：`tools/three_lane_scheduler.py`。**NOT_DEPLOYED**。

## 优先级 + 配额

- **优先级**（高→低）：`realtime > catchup > backfill`。realtime **总是先满足**。
- **配额** `BASE_QUOTA`（健康时）：realtime 0.6 / catchup 0.25 / backfill 0.15。

## 背压模型 + 自动暂停

每个活跃的 catchup/backfill 单元与 realtime 争用同一 Worker 子请求/CPU 预算，抬高 realtime freshness P95
（`INFLATION`：catchup 0.04、backfill 0.05 / 单元 / 基线）。`schedule(capacity, demand, baseline, kill_switch)`：
1. realtime 先满足；2. 按配额给 catchup、backfill；
3. **背压**：只要投影 realtime P95 > 基线×1.20，就**逐步撤销 backfill（自动暂停）**，仍超则**节流 catchup**，直到 P95 ≤ 天花板。
- **kill switch**：`kill_switch=True` → backfill 直接 0。

`Decision{alloc, realtime_p95, within_ceiling, backfill_paused, catchup_throttled, reason}`。
`backfill_paused` = 请求了但全被拒；`backfill_throttled` = 部分授予。

## 验收（`test-results/scheduler_tests.txt`，PASS）

压力测试 baseline=10、capacity=20、天花板=12（+20%）：
| 场景 | backfill 需求→授予 | realtime P95 | within | backfill_paused |
|---|---|---|---|---|
| healthy | 3→3 | 11.9 | ✓ | 否（正常跑） |
| backfill_pressure | 8→2 | 11.8 | ✓ | 否（节流） |
| heavy_realtime_burst | 6→**0** | 11.6 | ✓ | **是（自动暂停）** |
| kill_switch | 5→**0** | 10.8 | ✓ | 是 |

- **不变量**：**每个场景 realtime P95 ≤ 基线+20%**，且 realtime **总被完整服务**（不被下位车道饿死）。
- **超阈值自动暂停 backfill**：realtime 突发时 backfill 6→0 自动暂停；backfill 授予随压力上升**单调不增** [3,2,0]；kill switch 立即暂停。

## 边界

freshness 模型为结构性背压模型（每单元固定 inflation）；真实 P95 由真实 Worker 负载测得，接线时以真实基线校准。调度器未接生产 cron（NOT_DEPLOYED）；与 T041 planner 联动的落库/执行属云端接线后续。
