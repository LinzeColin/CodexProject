# 2026-06-13 Parallel Review Summary

本轮按用户要求分成 3 个独立审查方向：安全/质量/潜在 bug/并发/测试/维护性，压力与流程有效性，UI/交互/功能架构优化。结论是：本轮发现的问题中有 4 类属于合并前必须处理，已完成修复并验证；仍有 3 类产品能力未完成，继续作为下一阶段任务。

## 审查汇总

| 方向 | 发现的问题 | 严重程度 | 阻塞合并 | 修复状态 | 建议修复方式 |
| --- | --- | --- | --- | --- | --- |
| 安全 | 本地 `/api/*` POST 缺少 Origin/CSRF/action token，任意网页可能向 `127.0.0.1:8767` 发起本地操作 | High | 是 | 已修复 | 增加 per-process action token、Host/Origin/Referer 本地校验，前端所有 POST 附带 `X-TAB-FIFA-Action-Token` |
| 安全 | My Bets 私有持仓可写入 public `outputs/private/**`，且 safety 扫描跳过 `private` 路径 | High | 是 | 已修复 | 私有快照目录拒绝 public outputs；public artifact scan 递归检测 `tab_my_bets_positions_*.json` |
| 安全/合规 | TAB public raw 明确拒绝 AI controlled access，不能用 headed fallback 或规避方式恢复 | High | 是 | 已保持 fail-closed | raw/live discovery 返回 access-policy blocked；只允许官方/授权 feed、用户导出导入、或 existing fresh partial raw research-only |
| 潜在 bug | GitHub worktree 下 fixed parent-depth 输出根目录会指向错误 `github_sync/outputs` | High | 是 | 已修复 | 新增 `tab_research.paths`，统一解析 workspace/output/private 目录并支持 env override |
| 并发/竞态 | 后台任务 PID 由 shell 异步写入，可能出现重复启动或 PID stale | Medium | 否 | 已修复 | 启动路径加锁，父进程写 PID |
| 测试稳定性 | canonical output guard 测试依赖旧目录层级且会受缺失 Playwright 影响 | Medium | 否 | 已修复 | 测试显式设置 `TAB_FIFA_OUTPUT_DIR`，验证 guard 早于依赖加载 |
| 测试稳定性 | partial raw 测试固定时间戳会随时间变 stale | Medium | 否 | 已修复 | 测试使用当前 UTC 时间构造 fresh manifest |
| UI/交互 | 主动测试点击后可先显示缓存，但 blocked 场景文案错误声称已补写 research-only | Medium | 否 | 已修复 | backfill 文案按 `ready/status` 条件输出，browser smoke 验证 `未达到 ready` |
| UI/交互 | 页面导航、首屏推荐下注、市场资金分析、主动测试入口需要更像决策工作台 | Medium | 否 | 已完成上一阶段并复验 | 保留 EVA OS 风格工作台和锚点导航 |
| 功能完整 | 用户导出 raw snapshot importer / publish preflight | High | 是，阻塞正式 automation | Preview 与签名预检已完成；正式 publish 命令未完成 | 已实现导入 schema、校验、preview raw、稳定 hash、签名预检；下一阶段实现显式 publish 命令和 raw health/readiness 重算 |
| 功能完整 | Australia Markets 仍 route mismatch/unavailable | High | 是，阻塞 5/5 raw | 未完成 | 继续做 route/deep-link 发现；找不到则保持 unavailable/no-bet |
| 功能完整 | My Bets 真实持仓仍需用户本机授权登录 | Medium | 是，阻塞持仓收益率自动更新 | 未完成 | 让用户在本机 TAB 窗口完成登录，系统只读导入，不保存凭据 |

## 已验证命令

```bash
PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-review python3 -m unittest tests.test_pipeline
node --check scripts/refresh_tab_readonly.mjs
node --check scripts/discover_tab_live_boards.mjs
node --check scripts/capture_tab_my_bets_readonly.mjs
node scripts/refresh_tab_readonly_security.test.mjs
node scripts/capture_tab_my_bets_readonly_security.test.mjs
bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh scripts/verify_fifa_automation_readiness.sh
TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py
```

结果：Python `155 tests OK`；Node/security/bash checks 通过；Downloads app 入口已重建；本地服务 `http://127.0.0.1:8767/` 从 GitHub worktree 运行。

## 当前合并判断

可合并当前 hardening 分支/提交。合并后系统仍不是完整正式 automation，原因不是本轮代码质量问题，而是外部数据与授权边界仍未满足：

- current public raw: blocked by `ai_controlled_access_rejected`
- research scope: 4/5
- Australia Markets: unavailable / route mismatch
- private My Bets: login required
- current executable new stake: AUD 0
