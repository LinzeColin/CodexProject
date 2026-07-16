# Phase 6.3 风险与回滚

## 风险

- 部署服务器若不能对 canonical path 执行 SPA fallback，直接深链可能返回服务器 404；本 Phase 已在正式 Shell 的临时 loopback fallback 上验证，真实安装/部署环境仍须在 Stage 6 whole review 与最终发布验证。
- `about:srcdoc`/`file:` 无法安全改写 pathname，因此保留 hash compatibility fallback；它不是新的 canonical route。
- 浏览器 history state、session scroll memory 和 URL 若被外部脚本篡改，runtime 以 URL 为事实源并重写当前 entry；无法匹配时显示可行动 invalid-route 页面。
- 本 Phase 的 WCAG 证据聚焦一级导航、键盘进入、heading focus 与命名节点；完整跨页面 WCAG 2.2 AA 审计仍需 Stage 6 whole review 独立复核。

## 回滚

1. revert 本 Phase 单一实现提交。
2. 恢复 Phase 6.2 的 hash runtime 与 frontend hash，但保留 10 个一级入口、45 个 page contracts 和 no-JS fallback。
3. 不恢复旧 16 入口、title-only page clone 或重复策略实验室 route。
4. 不触碰真实财务数据、数据库、GitHub main 或已安装 App。

## 当前边界

- Phase 6.3=`candidate_pass`；Stage 6 whole-stage review/user acceptance=`not_started/waiting`。
- `finder_used=false`，`external_network_performed=false`，`push_performed=false`，`app_install_performed=false`。
