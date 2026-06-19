# 独立审查 B：压力、极限交互、流程、结果与运行生命周期

> 审查口径：本文件由一个独立审查单元形成，不引用其他审查单元的结论作为证据。严重度按 CRITICAL/HIGH/MEDIUM/LOW；“阻塞合并”区分本 Task Pack 基线与未来生产发布。

## 结论

原包仅有 happy-path smoke test，不能证明并发发布、快速递归切换、畸形状态、重复执行、退出清理和结果隔离。v5 新增浏览器韧性测试与自主运行器生命周期测试，覆盖当前原型和脚本可验证范围；真实后台调度、百万级图、服务端保存和 24 小时稳定性仍属于生产阻塞。

## 本次已执行的极限测试

1. 60 次连续 NVIDIA/TSMC/ASML 主体切换，最终焦点与 busy 状态稳定。
2. 12 次连续模型发布调用，仅形成一次版本与审计记录。
3. 140 条恶意/畸形日志输入被限制为 100，脚本/图片/SVG 不执行。
4. Microsoft 未接入数据集时不可切换，不再显示 NVIDIA 关系。
5. 两个自主运行实例竞争时，仅一个获得锁；运行结束后锁、子进程和临时缓存被清理。
6. 每个阶段输出进入独立 run 目录并通过原子复制生成兼容输出。
7. 浏览器测试使用单一 Chromium、隔离 Context、PASS sentinel 与独立进程组 supervisor；完成后清理 Playwright/Chromium/crashpad 后台进程。

## 发现明细

| ID | 严重度 | 状态 | 发现 | 是否阻塞生产 | 建议/处理 |
|---|---|---|---|---|---|
| STRESS-001 | HIGH | FIXED_IN_V5 | 无快速递归切换竞态测试 | YES | focus transition token 和 60 次循环压力测试 |
| STRESS-002 | HIGH | FIXED_IN_V5 | 无自动启动-执行-退出-缓存清理验证 | YES | runner dry-run 生命周期测试覆盖锁、输出、状态和清理；浏览器与 runner 在独立 CI Job 运行 |
| STRESS-003 | HIGH | FIXED_IN_V5 | 畸形持久化状态可破坏页面或放大资源消耗 | YES | 统一状态归一化和审计日志上限 |
| STRESS-004 | HIGH | FIXED_IN_V5 | 无递归对象数据隔离测试 | YES | 未接入对象禁用；独立数据集标志 |
| STRESS-005 | HIGH | FIXED_IN_V5 | 发布重复触发造成版本竞态 | YES | busy lock/token |
| STRESS-006 | MEDIUM | PARTIAL_V5 | 本地存储失败缺少明确反馈；生产缓存策略尚无实现 | YES | 原型提示失败；生产需 quota、TTL、namespacing、server persistence |
| STRESS-007 | CRITICAL | OPEN_PRODUCTION | 尚无真实调度器、自动唤醒、幂等运行、重试和关闭协议 | YES | 实现 job lease、idempotency key、heartbeat、graceful shutdown、dead-letter |
| STRESS-008 | HIGH | OPEN_PRODUCTION | 未验证 10k/100k/1m 节点边查询、布局与渲染预算 | YES | 建立分层基准、服务端子图、聚合、虚拟化、Web Worker/GPU 方案 |
| STRESS-009 | MEDIUM | OPEN_PRODUCTION | 未覆盖 768 以下、触屏、高 DPI、缩放 200%、长文本和 IME | YES | 建立设备矩阵与视觉回归 |
| STRESS-010 | HIGH | OPEN_PRODUCTION | 模型重算仍是动画模拟，未验证全局一致快照 | YES | 数据库事务/版本指针/缓存失效/事件确认 |
| STRESS-011 | HIGH | OPEN_PRODUCTION | 保存视图只存在本地状态，无版本、冲突和恢复语义 | YES | 服务端 saved_view、optimistic concurrency、版本历史 |
| STRESS-012 | MEDIUM | OPEN_PRODUCTION | 无 4h/24h soak、内存泄漏、计时器和 listener 泄漏测试 | YES | 加入浏览器与 worker soak suite |

## 合并判断

- **v5 Task Pack 基线：可合并**。
- **生产运行：不可合并**，直到调度租约、幂等键、heartbeat、graceful shutdown、服务端保存、负载与 soak 测试完成。
