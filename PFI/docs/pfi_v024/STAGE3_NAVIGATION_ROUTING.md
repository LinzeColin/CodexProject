# PFI v0.2.4 Stage 3 Phase 3.1 Navigation Contract

本轮只执行：`Stage 3 / Phase 3.1 - 导航合同`。
本轮不执行 Phase 3.2 路由实现、不执行 Phase 3.3 浏览器历史验收、不执行 Stage 3 whole-stage review、不上传 GitHub main。

## Scope

Phase 3.1 固定当前 v0.2.4 修补包的一级导航合同：

1. 正式一级入口固定为 10 个。
2. `市场与研究` 是第 9 个正式一级入口。
3. v0.1 旧入口 `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` 只能作为二级入口、alias 或 command 使用。
4. 页面不得出现底部或侧边栏 16 个同级入口堆叠。
5. active state 规则只允许一个正式一级入口处于 active；旧 alias 先解析到正式工作区，再更新 active workspace。

## Contract Artifacts

| Artifact | Purpose |
| --- | --- |
| `PFI/src/pfi_v02/stage_v024_stage3_navigation.py` | 机器可读 Phase 3.1 导航合同。 |
| `PFI/web/app/navigation.js` | Web Shell 当前 v0.2.4 Stage 3 导航合同读模型。 |
| `PFI/web/app/routes.js` | 保留 v0.2.3 历史导出，同时暴露 v0.2.4 Phase 3.1 route compatibility contract。 |
| `PFI/web/index.html` | 加载 `navigation.js`，并保持 desktop/mobile/no-js 只有 10 个一级入口。 |
| `PFI/src/pfi_os/app/streamlit_app.py` | 在 PFI.app / localhost 的 Streamlit embed 中内联 `navigation.js`。 |
| `PFI/tests/test_v024_stage3_phase31_navigation_contract.py` | Phase 3.1 合同、HTML、JS、Streamlit embed 和 evidence 测试。 |

## Official Primary Entries

| Index | Label | Workspace | Route |
| --- | --- | --- | --- |
| 1 | 首页总览 | `home` | `/home` |
| 2 | 账户与资产 | `accounts` | `/accounts` |
| 3 | 账本流水 | `ledger` | `/ledger` |
| 4 | 投资管理 | `investment` | `/investment` |
| 5 | 消费管理 | `consumption` | `/consumption` |
| 6 | 数据源与上传 | `sync` | `/sources-upload` |
| 7 | 建议与复盘 | `recommendations` | `/review` |
| 8 | 报告与洞察 | `insights` | `/reports` |
| 9 | 市场与研究 | `market_research` | `/market-research` |
| 10 | 设置 | `settings` | `/settings` |

## v0.1 Alias Policy

| Old Label | Public Alias | Resolved Route | Target Workspace | Primary Entry |
| --- | --- | --- | --- | --- |
| 首页 | `/home/today` | `/home` | `home` | not allowed |
| 市场 | `/market/watch` | `/market-research?tab=market` | `market_research` | not allowed |
| 研究 | `/market/research` | `/market-research?tab=research` | `market_research` | not allowed |
| 持仓 | `/investment/holdings` | `/investment?tab=holdings` | `investment` | not allowed |
| 策略实验室 | `/market/lab` | `/market-research/strategy-lab` | `market_research` | not allowed |
| 数据与系统 | `/settings/data` | `/settings?tab=data-system` | `settings` | not allowed |

## Acceptance Result

- Desktop primary nav count: 10.
- Mobile primary nav count: 10.
- No-js fallback primary route count: 10.
- Command palette keeps v0.1 labels as aliases.
- `navigation.js` loads before `routes.js`.
- Streamlit embed inlines `navigation.js` before `routes.js` and `shell.js`.
- v0.2.3 `PFI_V023_STAGE3_NAV` compatibility remains available in `routes.js`.

## Explicitly Not Done

- Phase 3.2 route implementation and browser route mutation are not completed in this run.
- Phase 3.3 browser back/forward/direct URL validation is not completed in this run.
- Stage 3 whole-stage review is not completed in this run.
- GitHub main upload is not completed in this run.
- No app bundle reinstall, launcher source change, or financial data logic change was made.
