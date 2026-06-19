# 并行独立审查汇总与迭代决策

## 结论

三个审查单元共登记 **40** 项：CRITICAL 6、HIGH 21、MEDIUM 12、LOW 1。v5 已修复或部分修复 24 项；仍有 16 项明确阻塞生产发布。

| 决策对象 | 结论 | 条件 |
|---|---|---|
| v5 Task Pack / GitHub 基线 | **允许合并** | preflight、浏览器、品牌、bundle parity、runner lifecycle 全部通过 |
| fixture 原型公开宣称为生产系统 | **禁止** | 数据库、API、真实数据、评分和刷新均未生产实现 |
| Codex 进入下一阶段 | **允许进入 Phase 0/1** | 一次一个 Issue；先只读计划；不得跨 Gate 自主扩张范围 |
| 生产 MVP 发布 | **阻塞** | 关闭全部 CRITICAL/HIGH production blockers 并附 Acceptance 证据 |

## 已在 v5 修复的合并阻塞项

- 持久化 DOM 注入路径。
- 畸形/越界本地状态。
- Microsoft/Meta 错误复用 NVIDIA 数据。
- embedded/external JS/CSS 漂移。
- 模型发布重复触发竞态。
- Codex 自主运行重入、覆盖、无清理和无检查点。
- Playwright/Chromium 关闭阶段可能残留进程树或占用 CI 输出描述符；新增单浏览器隔离 Context 与独立进程组 supervisor。
- 原型把 fixture 伪装为生产健康指标。
- 未清权 Atlas 类品牌继续渗透 UI/数据库/导出。

## 仍阻塞生产的最短清单

- **ARCH-001 CRITICAL**：当前仍是单文件 fixture 原型，无生产数据库；修复：按 DDL/迁移实现 PostgreSQL，事实/证据/时间/版本分层
- **ARCH-002 CRITICAL**：无生产 API、图查询、评分和刷新服务；修复：实现受契约约束的 API/graph query/scoring/config snapshot 服务
- **ARCH-003 CRITICAL**：无真实采集、实体解析和证据管线；修复：先完成半导体 Golden Vertical 的端到端真实数据管线
- **STRESS-007 CRITICAL**：尚无真实调度器、自动唤醒、幂等运行、重试和关闭协议；修复：实现 job lease、idempotency key、heartbeat、graceful shutdown、dead-letter
- **STRESS-008 HIGH**：未验证 10k/100k/1m 节点边查询、布局与渲染预算；修复：建立分层基准、服务端子图、聚合、虚拟化、Web Worker/GPU 方案
- **STRESS-009 MEDIUM**：未覆盖 768 以下、触屏、高 DPI、缩放 200%、长文本和 IME；修复：建立设备矩阵与视觉回归
- **STRESS-010 HIGH**：模型重算仍是动画模拟，未验证全局一致快照；修复：数据库事务/版本指针/缓存失效/事件确认
- **STRESS-011 HIGH**：保存视图只存在本地状态，无版本、冲突和恢复语义；修复：服务端 saved_view、optimistic concurrency、版本历史
- **STRESS-012 MEDIUM**：无 4h/24h soak、内存泄漏、计时器和 listener 泄漏测试；修复：加入浏览器与 worker soak suite
- **UX-003 MEDIUM**：若干导航别名聚合到同一页面，用户会误认为独立功能已实现；修复：生产版使用真实路由；未实现入口禁用或标注“规划中”
- **UX-007 MEDIUM**：模型/数据/治理页信息密度高，缺少用户任务优先级和渐进披露实测；修复：首屏保留决策信息；高级字段抽屉/二级页；可保存布局
- **UX-008 HIGH**：真实大图下固定坐标和首屏覆盖指标可能形成“毛线团”或被装饰性元素游戏化；修复：服务器子图、关系预算、聚合节点、语义缩放、等价列表
- **UX-009 HIGH**：筛选、深度、地区、比较、固定、展开等控件多为 toast-only；修复：实现真实状态/查询/API；未完成前禁用并标注
- **UX-010 HIGH**：原型的关系证据摘要仍是 fixture，缺少原文片段、冲突证据和来源版本；修复：证据抽屉包含来源、片段、时间、解析器、置信度、反证和审核状态
- **UX-011 HIGH**：UI 状态、图查询、模型配置、数据版本尚未形成单一上下文契约；修复：定义 WorkspaceContext: focus/filter/time/config/data snapshot/path
- **UX-012 MEDIUM**：单文件原型不可直接作为生产组件架构；修复：拆分 shell、graph、inspector、model center、data workbench、state/query 层

## Codex 推荐执行顺序

1. `CURRENT_PHASE.md` 的 Phase 0：架构与范围冻结。
2. 工程底座与真实 PostgreSQL 迁移。
3. 半导体 Golden Vertical 的真实来源、实体解析与证据链。
4. 递归图查询与 WorkspaceContext。
5. 模型配置版本、原子刷新和回滚。
6. 生产 UI、全状态交互、性能/可访问性。
7. 压力、soak、灾难恢复和发布 Gate。

## 防回归规则

所有修复必须同步 `data/review_issue_register.csv`、任务状态、Acceptance ID、风险登记和测试证据；不得仅在总结文档中宣称完成。
