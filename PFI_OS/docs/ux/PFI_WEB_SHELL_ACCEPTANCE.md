# PFI Web Shell Acceptance

Version: PFI-004

PFI Web Shell is the new user-facing skeleton for PFI OS. It is intentionally
thin in this slice: it frames the product, preserves global context, shows
cached homepage content, and exposes feedback states without migrating legacy
business pages.

## Scope

- Six primary workspaces: 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统.
- Top bar: product identity, global search, market/entity/portfolio/as-of
  context, sync status, task center, notification surface, settings entry.
- Right drawer: evidence, source, model, parameters, data lineage, raw document.
- Homepage: cached summary, freshness, decision queue, compact table controls,
  and recoverable feedback states.
- Feature flag: `PFI_UI_V2=1` opens the new shell; `PFI_UI_V2=0` keeps the
  migration fallback.

## Non-Scope

- No business-page migration.
- No backtest kernel rewrite.
- No local model integration.
- No Docker or separate web/api/worker startup.
- No live automatic order route.

## Acceptance

- Contract tests verify the six workspaces, feature flag, global context,
  evidence sections, safety boundary, and no retired user text.
- E2E static-flow tests verify localStorage context persistence, no full-page
  reload, command palette navigation, task center, evidence drawer, table
  controls, and recoverable cache fallback.
- Visual tests verify layout regions, theme tokens, 44px targets, skeleton,
  drawer, compact table, canvas chart, and screenshot baseline metadata.
