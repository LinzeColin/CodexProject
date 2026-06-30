# PFI v0.2.4 Stage 3 Navigation Routing

当前已完成至：`Stage 3 GitHub main upload gate`。
GitHub main upload 由独立 terminal gate 验证。

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
| `PFI/tests/test_v024_stage3_phase32_route_implementation.py` | Phase 3.2 route 解析、redirect 和 runtime 声明测试。 |
| `PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py` | Phase 3.3 浏览器验收 evidence 合同测试。 |
| `PFI/scripts/validate_v024_stage3_phase33_browser.js` | Phase 3.3 Node Playwright 真实浏览器验收脚本。 |
| `PFI/docs/pfi_v024/STAGE3_WHOLE_STAGE_REVIEW.md` | Stage 3 整阶段复审报告。 |
| `PFI/tests/test_v024_stage3_whole_review_contract.py` | Stage 3 整阶段复审合同测试。 |

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

### Phase 3.1

- Desktop primary nav count: 10.
- Mobile primary nav count: 10.
- No-js fallback primary route count: 10.
- Command palette keeps v0.1 labels as aliases.
- `navigation.js` loads before `routes.js`.
- Streamlit embed inlines `navigation.js` before `routes.js` and `shell.js`.
- v0.2.3 `PFI_V023_STAGE3_NAV` compatibility remains available in `routes.js`.

### Phase 3.2

- `PFI/web/app/routes.js` exposes `window.PFI_V024_STAGE3_ROUTES`.
- Primary route table resolves all 10 official first-level routes.
- Secondary route table resolves 45 owned second-level routes across the 10 workspaces.
- v0.1 alias routes redirect to owned v0.2.4 routes:
  - `/home/today` -> `/home`
  - `/market/watch` -> `/market-research?tab=market`
  - `/market/research` -> `/market-research?tab=research`
  - `/investment/holdings` -> `/investment?tab=holdings`
  - `/market/lab` -> `/market-research/strategy-lab`
  - `/settings/data` -> `/settings?tab=data-system`
- `PFI/web/app/shell.js` uses `PFI_V024_STAGE3_ROUTES.resolveRouteAlias()` before fallback route parsing.
- Runtime declarations exist for hash routes, `pushState`, `replaceState`, `hashchange`, and `popstate`.
- Browser back/forward validation is completed by Phase 3.3 evidence.

### Phase 3.3

- Node Playwright browser validation contract: `PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION`.
- Real browser DOM found exactly 10 desktop primary entries and 10 mobile primary entries.
- `市场与研究` remains `data-nav-index="9"`.
- v0.1 labels `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` are absent as exact primary entries.
- Browser route API resolves all 6 v0.1 legacy aliases as `legacy_redirect`.
- Direct URL aliases such as `#/market/watch` replace to owned v0.2.4 routes such as `#/market-research?tab=market`.
- Click navigation across primary routes passes.
- Browser back/forward across `/accounts` -> `/market-research` -> `/settings` passes.
- Screenshots are recorded at:
  - `PFI/reports/pfi_v024/stage_3/phase_3_3/screenshots/desktop_nav.png`
  - `PFI/reports/pfi_v024/stage_3/phase_3_3/screenshots/browser_back_after_forward.png`
- Browser JSON evidence is recorded at:
  - `PFI/reports/pfi_v024/stage_3/phase_3_3/browser_validation.json`
  - `PFI/reports/pfi_v024/stage_3/phase_3_3/legacy_routes_validation.json`

### Whole-Stage Review

- Reviewed Phase 3.1, Phase 3.2, and Phase 3.3 evidence.
- Reran Node Playwright browser validation at review time.
- Fixed the missing whole-stage review contract/evidence gate.
- Fixed top-level status files that still pointed at Phase 3.3 as the current gate.
- Refreshed Phase 3.3 browser validation JSON and screenshot evidence.
- Review evidence is recorded at:
  - `PFI/reports/pfi_v024/stage_3/whole_stage_review/evidence.json`

## Explicitly Not Done

- GitHub main upload is handled by `STAGE3_GITHUB_MAIN_UPLOAD.md` and terminal remote verification.
- Stage 4 is not started.
- No app bundle reinstall, launcher source change, or financial data logic change was made.
