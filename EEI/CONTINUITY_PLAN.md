# 开发连续性与稳定性计划

## 阶段链

| 阶段 | 目标 | 主要退出证据 |
|---|---|---|
| 0 | 目标/品牌/架构冻结 | ADR、Issue 映射、基线校验 |
| 1 | 可运行工程底座 | clean-room bootstrap、CI、健康检查 |
| 2 | PostgreSQL/领域本体/证据模型 | migration/rollback/完整性测试 |
| 3 | 真实数据与 Golden Vertical | 来源-事实-证据端到端追溯 |
| 4 | 图查询、递归探索、WorkspaceContext | NVIDIA→TSMC→ASML 深链恢复 |
| 5 | 模型配置、原子重算与回滚 | config_version 全局一致 |
| 6 | 生产 UI/UX、全状态与可访问性 | 关键任务、性能、视觉回归 |
| 7 | 资本/政策/战略/时间智能 | 推断链、反证与不确定性 |
| 8 | 压力、soak、安全、备份与发布 | P95/P99、恢复演练、Gate |
| 9 | 行业扩张与双周校准 | 数据质量/模型漂移报告 |

## 每个 Issue 的固定闭环

`Plan(read-only) → bounded diff → unit/contract/e2e → risk/acceptance update → reviewer evidence → merge → checkpoint`

## GitHub 防漂移

功能、模型、参数、阈值、关系、供应链、行业、公司、任务、风险和 Acceptance 的修改必须在同一 PR 同步人类文档、机器目录、测试和变更日志。

## 自动运行边界

`scripts/run_codex_autonomous.sh` 提供单实例锁、独立 run 目录、状态 JSON、检查点、超时、信号处理、原子输出和临时缓存清理。它不能代替人工批准 G0，也不能自动绕过生产阻塞项。
