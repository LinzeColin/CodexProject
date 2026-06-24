# 审查轨 B｜压力、极限流程、运行与自动生命周期

## 结论

本轨发现 **16** 项：P0=3、P1=12、P2=1、P3=0。P0 全部阻塞生产/最终集成；P1 阻塞受影响范围。

## 审查范围

覆盖负载/压力/峰值/浸泡/故障注入、自动唤醒、自动运行、优雅关闭、后台清理、缓存、数据保存、恢复和 3+1/周/月端到端。

## 独立方法

以“可启动、可终止、可恢复、可证明”为验收轴；只把真实执行过的定向探针标为 reproduced，未执行的生产场景明确标 not_verified。

## 问题总表

| ID | 问题 | 严重度 | 合并阻塞 | 证据 | 修复 Task |
|---|---|---:|---|---|---|
| `B-001` | 自动唤醒/安装/卸载当前只有 dry-run 模板，不是可验收功能 | **P0** | `global` | static_confirmed：stage1_runtime.py:371-417,420-447 明确 dry_run_only/applied=false | `S2PMT04` |
| `B-002` | 缺少统一进程生命周期：STARTING/RUNNING/DRAINING/CHECKPOINTING/STOPPED | **P1** | `scope` | design_gap：当前 runtime 只有 tick/watchdog 文件，没有 drain/shutdown contract | `S2PMT04` |
| `B-003` | watchdog 只报告 stale lock，不执行可证明安全的恢复 | **P1** | `scope` | static_confirmed：stage1_runtime.py:169-215 | `S2PMT03` |
| `B-004` | 启动时没有在途任务、outbox、临时文件和残锁 reconciliation | **P1** | `scope` | design_gap：V7.0 生命周期合同未定义 startup reconciliation | `S2PMT04` |
| `B-005` | 无安全缓存分类、TTL、容量上限、清理与保留证据 | **P1** | `scope` | design_gap：任务包未定义 cache housekeeping | `S2PMT04` |
| `B-006` | 缺少正式负载、压力、峰值、浸泡和容量基线 | **P1** | `scope` | not_verified：本轮仅执行 64 tick 和 120 SQLite 写入定向探针，非全系统压力测试 | `S2PMT05` |
| `B-007` | 没有双调度器/双 worker/重复触发的生产级竞态测试 | **P0** | `global` | not_verified：现有定向 P08 仅验证同进程线程下简单 lock | `S2PMT05` |
| `B-008` | 没有“SMTP 已接受但本地未提交”崩溃窗口测试 | **P0** | `global` | not_verified：对应 A-003 外部副作用窗口 | `S2PMT05` |
| `B-009` | 缺少磁盘满、只读目录、数据库锁死、损坏缓存/备份等故障注入 | **P1** | `scope` | not_verified：现有测试矩阵未列出系统性 fault injection | `S2PMT05` |
| `B-010` | 缺少 Australia/Sydney DST、时钟跳变、漏跑和补跑政策测试 | **P1** | `scope` | design_gap：schedule 以自由文本时间表示，无 misfire/catch-up/ambiguous-time policy | `S2PMT05` |
| `B-011` | M4 水位线缺少 cycle_id、超时、迟到数据和降级策略 | **P1** | `scope` | design_gap：product_contract_v7.yaml 只有 requires_terminal: M1-M3 | `S2PMT03` |
| `B-012` | 没有覆盖 3+1 日报、周报、月报、复习、行动、ROI 的完整流程测试 | **P1** | `scope` | not_verified：V7.0 测试矩阵为高层描述，无可执行 E2E 命令 | `S2PMT05` |
| `B-013` | 结果有效性测试偏结构存在性，缺语义、证据和非模板化验收 | **P1** | `scope` | static_confirmed：lesson/report 当前验证主要检查字段、中文字符、marker | `S2PHT05` |
| `B-014` | 无背压、熔断、降级和负载丢弃优先级 | **P1** | `scope` | design_gap：队列容量存在，但没有过载策略合同 | `S2PMT05` |
| `B-015` | 后台清理与数据保存没有事务边界和可观察完成信号 | **P1** | `scope` | design_gap：heartbeat/checkpoint 分别直接写文件，无 durable shutdown receipt | `S2PMT04` |
| `B-016` | 缺少 fake clock、fake network、随机种子和资源隔离，测试易波动 | **P2** | `no` | design_gap：generated_at 由调用者自由传入，网络/SMTP 测试合同未统一 | `S2PMT05` |

## 逐项整改要求

### B-001｜自动唤醒/安装/卸载当前只有 dry-run 模板，不是可验收功能

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** static_confirmed；stage1_runtime.py:371-417,420-447 明确 dry_run_only/applied=false
- **影响：** 无法证明系统会在目标机器自动唤醒、自动运行、自动关闭并在重启后恢复。
- **建议修复：** 提供受控 install/status/uninstall 三态；平台适配器；安装后验收实际触发一次；默认关闭副作用；Owner 明确启用。
- **必须测试：** 隔离 VM/容器/测试账号上安装→触发→状态→卸载完整通过
- **归属 Task：** `S2PMT04`

### B-002｜缺少统一进程生命周期：STARTING/RUNNING/DRAINING/CHECKPOINTING/STOPPED

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；当前 runtime 只有 tick/watchdog 文件，没有 drain/shutdown contract
- **影响：** 收到 SIGTERM、系统睡眠、更新或超时时，无法安全停止新任务、完成/回滚在途工作。
- **建议修复：** 实现 lifecycle state machine；信号处理；grace period；停止 claim；flush outbox/DB；checkpoint；release lease；退出码。
- **必须测试：** 每个阶段注入 SIGTERM/SIGINT，重启后无丢失/重复不可控副作用
- **归属 Task：** `S2PMT04`

### B-003｜watchdog 只报告 stale lock，不执行可证明安全的恢复

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** static_confirmed；stage1_runtime.py:169-215
- **影响：** 后台异常后可能永久停止，必须人工删除锁且有误删活进程风险。
- **建议修复：** PID/host/boot_id/lease/fencing 验证；只有租约过期且 owner 不存活才接管；记录 recovery event。
- **必须测试：** 活进程慢任务不被误杀；死进程锁自动安全接管
- **归属 Task：** `S2PMT03`

### B-004｜启动时没有在途任务、outbox、临时文件和残锁 reconciliation

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；V7.0 生命周期合同未定义 startup reconciliation
- **影响：** 断电后 QUEUED/RUNNING/SENDING/WRITING 状态可能永久悬挂或重复执行。
- **建议修复：** 启动固定顺序：preflight→lease→schema→reconcile temp/outbox/inflight→resume/requeue→run。
- **必须测试：** 在每个持久状态断电后重启，状态最终收敛且计数守恒
- **归属 Task：** `S2PMT04`

### B-005｜无安全缓存分类、TTL、容量上限、清理与保留证据

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；任务包未定义 cache housekeeping
- **影响：** 磁盘可被全文/PDF/模型缓存耗尽；误清理可能删除原始证据或数据库。
- **建议修复：** 区分 durable evidence / rebuildable cache / temp；按类别 TTL+max_bytes；先 dry-run；路径白名单；删除日志；最低可用磁盘水位。
- **必须测试：** 路径穿越/符号链接不删；低磁盘自动降载；durable 目录永不清理
- **归属 Task：** `S2PMT04`

### B-006｜缺少正式负载、压力、峰值、浸泡和容量基线

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** not_verified；本轮仅执行 64 tick 和 120 SQLite 写入定向探针，非全系统压力测试
- **影响：** 无法知道四源突发、全文下载、模型延迟、3+1 邮件截止水位下是否稳定。
- **建议修复：** 建立 workload model 和 SLO；load→stress→spike→soak；记录 throughput、latency、queue age、memory、disk、error rate。
- **必须测试：** 至少 24h soak；2x 峰值；队列有界且可恢复
- **归属 Task：** `S2PMT05`

### B-007｜没有双调度器/双 worker/重复触发的生产级竞态测试

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** not_verified；现有定向 P08 仅验证同进程线程下简单 lock
- **影响：** GitHub/manual/local/重启补跑可能同时触发同一 cycle，导致重复报告和邮件。
- **建议修复：** 定义 cycle_id、唯一约束、leader lease/fencing、outbox；用多进程/多主机模拟并发。
- **必须测试：** 100 次重复 trigger 最终每个 M1-M4 只有一个 active revision 和一次受控投递
- **归属 Task：** `S2PMT05`

### B-008｜没有“SMTP 已接受但本地未提交”崩溃窗口测试

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** not_verified；对应 A-003 外部副作用窗口
- **影响：** 这是邮件重复最关键的故障窗口，未验证则不能生产启用。
- **建议修复：** 可编程 fake SMTP 在 accept 后阻塞/kill；重启 reconciliation；检查 outbox 和 Message-ID。
- **必须测试：** 每个发送阶段注入崩溃，重复率和最终状态符合明确合同
- **归属 Task：** `S2PMT05`

### B-009｜缺少磁盘满、只读目录、数据库锁死、损坏缓存/备份等故障注入

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** not_verified；现有测试矩阵未列出系统性 fault injection
- **影响：** 最常见本地运行故障可能造成静默停机、半文件或数据丢失。
- **建议修复：** pyfakefs/配额目录/fault injection adapter；所有持久写入 fail-closed 和原子。
- **必须测试：** ENOSPC/EACCES/SQLITE_BUSY/corrupt JSON/PDF/backup 均有明确状态和恢复路径
- **归属 Task：** `S2PMT05`

### B-010｜缺少 Australia/Sydney DST、时钟跳变、漏跑和补跑政策测试

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；schedule 以自由文本时间表示，无 misfire/catch-up/ambiguous-time policy
- **影响：** 夏令时切换、机器休眠或网络恢复时可能漏发或重复发。
- **建议修复：** 结构化 schedule(timezone, local_time, misfire_grace, catch_up, max_runs, fold policy)；cycle 使用本地业务日+UTC instant。
- **必须测试：** DST forward/backward、NTP 前后跳、休眠 8h 后补跑均确定性
- **归属 Task：** `S2PMT05`

### B-011｜M4 水位线缺少 cycle_id、超时、迟到数据和降级策略

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；product_contract_v7.yaml 只有 requires_terminal: M1-M3
- **影响：** M4 可能等待错日邮件、永久阻塞，或在迟到数据后无修订策略。
- **建议修复：** watermark keyed by cycle_id；终态枚举；deadline；degraded reason；late-arrival revision policy；M4 唯一键。
- **必须测试：** M2 失败/M3 超时/迟到/重跑/跨日均生成正确 M4 状态
- **归属 Task：** `S2PMT03`

### B-012｜没有覆盖 3+1 日报、周报、月报、复习、行动、ROI 的完整流程测试

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** not_verified；V7.0 测试矩阵为高层描述，无可执行 E2E 命令
- **影响：** 单模块通过后仍可能在跨功能连接处丢数据、断链接或计数不守恒。
- **建议修复：** 固定 35 日 fake clock 场景：每日四邮件、周报、月报、复习到期、行动、转化；核对全部 ledger。
- **必须测试：** 一条命令生成可审计 run bundle，分项总数守恒、链接可达
- **归属 Task：** `S2PMT05`

### B-013｜结果有效性测试偏结构存在性，缺语义、证据和非模板化验收

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** static_confirmed；lesson/report 当前验证主要检查字段、中文字符、marker
- **影响：** “格式齐全但没有新知识”的内容仍可通过。
- **建议修复：** 10 项金标双盲；claim entailment；引用定位；相似度/模板率；反证；个人行动可执行；回归阈值。
- **必须测试：** 金标五维≥4/5；关键事实人工抽检；模板重复率上限
- **归属 Task：** `S2PHT05`

### B-014｜无背压、熔断、降级和负载丢弃优先级

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；队列容量存在，但没有过载策略合同
- **影响：** 来源突发或模型变慢时队列无限老化，错过邮件窗口或挤占高价值任务。
- **建议修复：** 有界队列；priority aging；per-source quota；circuit breaker；降级到摘要级；deadline-aware shedding；告警。
- **必须测试：** 2x/5x 峰值下高优先项 SLO，低优先项明确延后/丢弃原因
- **归属 Task：** `S2PMT05`

### B-015｜后台清理与数据保存没有事务边界和可观察完成信号

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；heartbeat/checkpoint 分别直接写文件，无 durable shutdown receipt
- **影响：** 系统看似自动关闭，但状态、缓存、数据库和邮件进度可能尚未落盘。
- **建议修复：** drain receipt：claimed/inflight/outbox/db checkpoint/cache cleanup/backup/lease release 每步状态；失败保持 RECOVERING。
- **必须测试：** 关闭中每一步 kill，重启可从 receipt 精确恢复
- **归属 Task：** `S2PMT04`

### B-016｜缺少 fake clock、fake network、随机种子和资源隔离，测试易波动

- **严重程度：** P2（中风险质量/维护性级）
- **是否阻塞合并：** no
- **证据状态：** design_gap；generated_at 由调用者自由传入，网络/SMTP 测试合同未统一
- **影响：** 时间、网络和并发测试可能 flaky，无法稳定复现。
- **建议修复：** Clock/Network/SMTP/FileSystem adapters；固定 seed；每测试独立临时目录与数据库；禁止共享全局环境。
- **必须测试：** 同 seed 重跑完全一致；并行 pytest 无共享状态污染
- **归属 Task：** `S2PMT05`
