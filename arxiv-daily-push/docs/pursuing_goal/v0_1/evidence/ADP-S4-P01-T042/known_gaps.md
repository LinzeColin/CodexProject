# Known gaps · ADP-S4-P01-T042

- **NOT_DEPLOYED（任务边界，非缺陷）**：调度器 + 背压 + kill switch 是逻辑，未接生产 cron/worker。与 T041 planner 联动的真实落库执行属云端接线后续。
- **freshness 模型为结构性背压**：`INFLATION`（每单元固定抬高 P95）是**模型**，用于确定性演示「背压→自动暂停→realtime P95 守住 +20%」。**真实 P95** 由真实 Worker 负载测得；接线时须以真实基线（T023 已知 Worker 子请求~50/请求上限）校准 inflation 与 capacity。
- **capacity/quota 为抽象单元**：capacity=20、单元制；真实映射到 Worker 子请求/CPU 时间/每 run 抓取上限（DIR-007），接线时具体化。
- **kill switch 为参数**：`kill_switch=True` 立即暂停 backfill；生产接成手动/自动开关（超阈值自动 + 人工强制）属接线。
- **未含 catchup 车道细化**：catchup 车道作中优先级建模；真实 catchup（近期缺口补齐）的触发/范围随三车道接线细化。
