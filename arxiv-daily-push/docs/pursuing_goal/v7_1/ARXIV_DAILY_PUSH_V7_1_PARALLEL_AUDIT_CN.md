# 三轨并行审查汇总与合并结论

## 结论

**当前 V7.0 任务包可以继续作为需求基线，但不能作为“可直接生产合并”的交付。** 本轮共记录 **53** 项：P0=8、P1=37、P2=8；全局阻塞=8、范围阻塞=37、非阻塞=8。

Stage2 数据源连接器可继续在 Shadow/无最终邮件/无真实副作用条件下开发；以下能力在 P0 清零前禁止生产启用：真实 restore、真实 SMTP、自动调度安装、最终集成 Gate。

## 三轨结果

| 审查轨 | 问题数 | 核心结论 |
|---|---:|---|
| A 安全/代码/并发 | 22 | 恢复、外部副作用、证据边界和并发状态存在阻塞缺口 |
| B 压力/运行/生命周期 | 16 | 自动运行仍缺完整安装—运行—关闭—恢复证据，压力与故障矩阵未闭合 |
| C UI/交互/架构 | 15 | V7 关键要求尚未在 GitHub 形成可操作、可追踪、中文的人类控制面 |

## P0 必修清单

| ID | 问题 | 严重度 | 合并阻塞 | 证据 | 修复 Task |
|---|---|---:|---|---|---|
| `A-001` | 恢复清单允许路径穿越读取备份根目录外文件 | **P0** | `global` | dynamic_reproduced：Probe P04；stage1_runtime.py:302-337 | `S2PMT02` |
| `A-002` | 恢复先覆盖现有数据库、后验证，失败会破坏在线目标 | **P0** | `global` | dynamic_reproduced：Probe P05；stage1_runtime.py:348-367 | `S2PMT02` |
| `A-003` | SMTP 发送与持久状态之间没有事务发件箱 | **P0** | `global` | static_confirmed：smtp_delivery.py:64-99；发送完成后才返回内存报告 | `S2PMT03` |
| `A-004` | 邮件前台结论/机制/映射/行动绕过 Claim Ledger | **P0** | `scope` | dynamic_reproduced：Probe P14；lesson.py:126-156；validate_lesson_against_ledger 仅验证 sections | `S2PMT01` |
| `A-005` | 缺少不可信论文/网页内容的 Prompt Injection 与工具边界 | **P0** | `scope` | design_gap：V7.0 合同未定义 untrusted-content trust boundary | `S2PMT01` |
| `B-001` | 自动唤醒/安装/卸载当前只有 dry-run 模板，不是可验收功能 | **P0** | `global` | static_confirmed：stage1_runtime.py:371-417,420-447 明确 dry_run_only/applied=false | `S2PMT04` |
| `B-007` | 没有双调度器/双 worker/重复触发的生产级竞态测试 | **P0** | `global` | not_verified：现有定向 P08 仅验证同进程线程下简单 lock | `S2PMT05` |
| `B-008` | 没有“SMTP 已接受但本地未提交”崩溃窗口测试 | **P0** | `global` | not_verified：对应 A-003 外部副作用窗口 | `S2PMT05` |

## 合并决策

| 合并类型 | 当前决策 |
|---|---|
| Stage2 来源解析/fixture/Shadow | **可继续**，前提是不修改公共副作用和最终邮件路径，且读取 V7.1 合同 |
| restore/backup 生产路径 | **阻塞**，直到 A-001/A-002 关闭 |
| SMTP 真实发送 | **阻塞**，直到 A-003、B-008 关闭 |
| 自动调度安装与无人值守运行 | **阻塞**，直到 B-001、A-013、B-002～B-005 关闭 |
| 深度内容正式邮件 | **阻塞**，直到 A-004/A-005/A-019 与金标门关闭 |
| `INTEGRATED_PRODUCTION_ACCEPTED` | **阻塞**，直到 P0/P1=0 且 S2PMT07 独立复审通过 |

## 修复顺序

1. `S2PAT05`：把本审查与 V7.1 合同、Stop Code、任务依赖写入仓库。
2. `S2PMT01`：安全与证据边界。
3. `S2PMT02`：原子文件、备份与恢复。
4. `S2PMT03`：lease/fencing、状态并发与 transactional outbox。
5. `S2PMT04`：自动唤醒—运行—drain—关闭—清理生命周期。
6. `S2PMT05`：压力、浸泡、故障、DST 与 E2E 验证。
7. `S2PMT06`：中文 UI、交互反馈、导航与安全操作。
8. `S2PMT07`：独立复审、证据封包和最终 Gate。

## 验收口径

修复完成不等于代码存在。每项必须同时有：失败复现→修复 diff→自动测试→运行证据→三基/四查更新→回滚说明→下一 Agent 可读交接。
# 并行审查方法、范围与诚实边界

## 已实际完成

1. 对 V7.0 ZIP **37 个文件**做完整性、版本、YAML/CSV/Markdown 结构审查。
2. 对当前代码快照的 8 个关键模块做静态审查。
3. 执行 **19 个隔离定向探针**：通过 2，失败 17。
4. 执行 64 并发 tick 单实例探针和 120 项/24 线程 SQLite 写入探针。
5. 将全部问题绑定到严重度、合并政策、修复 Task、测试和交接证据。

## 未伪装成已完成

- 本包不是完整 Git 仓库，当前环境无法克隆全仓，因此没有运行全量 `pytest`、真实 SMTP、真实 OS 调度安装、真实四源网络压力或 24 小时 soak。
- “not_verified” 表示必须由 Codex 在完整仓库/隔离运行机执行，不等同于通过或失败。
- 定向探针使用隔离依赖 stub，只用于复现目标函数的边界行为，不替代集成测试。

## 证据等级

| 标记 | 含义 |
|---|---|
| `dynamic_reproduced` | 本轮以可执行探针复现 |
| `static_confirmed` | 代码/合同路径直接确认 |
| `design_gap` | 产品要求存在，但合同/实现未定义 |
| `not_verified` | 必须在完整环境执行，当前没有证据 |

## 合并原则

- P0/global：禁止生产启用、SMTP、真实 restore、调度安装、最终集成验收。
- P1/scope：阻塞所触及的 Task/文件/Phase；不触及公共接口和副作用路径的 Stage2 Shadow 连接器开发可继续。
- 任何“未测试”不得写成 PASS；任何修复必须有失败测试先行和回归证据。
