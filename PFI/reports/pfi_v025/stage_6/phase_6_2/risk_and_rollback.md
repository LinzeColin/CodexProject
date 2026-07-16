# Phase 6.2 风险与回滚

## 风险

- 旧 query route 若绕过 registry，可能使 URL 与页面状态分叉；当前通过 45 条历史映射与 canonical route 测试约束。
- 共享组件若覆盖页面合同，可能退化成只换标题；当前以唯一 layout signature、data object、primary action 和浏览器代表页验证约束。
- focus/scroll 恢复可能在完整 back/forward/reload 场景暴露时序差异；本 Phase 只证明页面切换恢复，完整矩阵留给 Phase 6.3。
- no-JS fallback 不加载动态数据；它只保证页面目录、任务与 canonical route 可读，不能替代启用 JavaScript 后的业务状态。

## 回滚

1. revert 本 Phase 单一实现提交。
2. 恢复 Phase 6.1 的 route registry 与 frontend hash。
3. 保留旧 query route snapshot 只作兼容；不得恢复旧 16 个一级入口或第二套 responsive DOM。
4. 不触碰 Stage 5 evidence、数据库、真实财务数据、GitHub main 或已安装 App。

## 当前边界

- Phase 6.2=`candidate_pass`；Phase 6.3 与 Stage 6 whole-stage review=`not_started`。
- `finder_used=false`，`external_network_performed=false`，`push_performed=false`，`app_install_performed=false`。
