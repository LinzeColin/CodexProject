# PFI v0.2.3 Stage 3 导航与路由

本文件记录 Stage 3 已完成 phase 的导航合同。Stage 3 总目标是把正式一级入口固定为 10 个，并让 v0.1 旧入口只作为兼容 route、二级入口、重定向或搜索命令存在。

## Phase 3.1 范围

- 桌面 `side-nav` 保持 10 个正式一级入口，顺序与 Task Pack 一致。
- 新增 `PFI/web/app/routes.js`，把 10 个正式入口和 v0.1 兼容入口归属写成可测试合同。
- 移动端底部入口从 5 个快捷入口改为 10 个正式一级入口，不再用“更多”桶承载旧入口。
- 点击桌面或移动端一级入口后，active 状态、主内容工作区和 route alias 同步更新。

## 正式一级入口

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察
9. 市场与研究
10. 设置

## Phase 3.2 兼容 route

本 phase 只交付 `Stage 3 Phase 3.2 — v0.1 兼容路由`。6 个旧入口不恢复为同层一级入口，只作为 public compatibility route 或命令入口存在，并解析到 v0.2.3 正式工作区：

| Task | v0.1 入口 | public route | 解析到 |
|---|---|---|---|
| T3.2.1 | 首页 | `/home/today` | `/home` |
| T3.2.2 | 市场 | `/market/watch` | `/market-research?tab=market` |
| T3.2.2 | 研究 | `/market/research` | `/market-research?tab=research` |
| T3.2.3 | 持仓 | `/investment/holdings` | `/investment?tab=holdings` |
| T3.2.4 | 策略实验室 | `/market/lab` | `/market-research/strategy-lab` |
| T3.2.4 | 数据与系统 | `/settings/data` | `/settings?tab=data-system` |

兼容 route 合同在 `PFI/web/app/routes.js` 中暴露，`PFI/web/app/shell.js` 使用同一合同生成命令别名并做 route normalize。浏览器验收记录在 `PFI/reports/pfi_v023/stage_3/phase_3_2/browser_validation.json`。

## Phase 3.3 浏览器行为

本 phase 只交付 `Stage 3 Phase 3.3 — 浏览器行为`。浏览器行为范围固定为：

- 点击一级入口后由 `pushState` 写入 hash route，并同步主工作区 state。
- `popstate`/`hashchange` 可恢复工作区、active 状态和 route state。
- 直接打开 hash route 或 `?route=` alias 时进入对应工作区。
- 浏览器脚本关闭时，`noscript` fallback 暴露 10 个正式一级入口 route 链接。

浏览器验收记录在 `PFI/reports/pfi_v023/stage_3/phase_3_3/browser_validation.json`，截图为 `screenshots/browser_history.png` 和 `screenshots/no_js_fallback.png`。

## 明确未做

已完成 phase 不做二级页面差异化、不做 Stage 3 整体复审、不上传 GitHub main。上述内容分别属于 Stage 4 或 Stage 3 整体复审。
