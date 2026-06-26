# PFI-005 Gate 2 Shell Acceptance

Last updated: 2026-06-20 Australia/Sydney

PFI-005 closes the user-facing Gate 2 gap that caused the shell to look like a
renamed legacy surface instead of a usable PFI product. The acceptance standard
is a browser-executed proof: real clicks must move through Chinese PFI panels,
core function blocks must open same-shell function views, and the shell must
not fall back to legacy page navigation for the primary workflows.

## Scope

- Product surface: PFI Web Shell embedded by Streamlit.
- Primary entrances: 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统.
- Core user workflows:
  - `JOURNEY_HOME_TO_BACKTEST`: 首页 -> 单标的回测.
  - `JOURNEY_STRATEGY_MARKET_FEEL`: 策略实验室 -> 盘感训练.
  - `JOURNEY_RESEARCH_REPORT_POLICY`: 研究 -> 报告清单 -> 政策雷达.
  - `JOURNEY_DATA_SYSTEM_DIAGNOSTICS`: 数据与系统 -> 数据中心.
- Non-goals: no Streamlit business-page rewrite, no broker/order/payment
  connection, no market refresh, no full release gate.

## Acceptance Contract

`scripts/pfiGate2ShellAcceptance.sh` writes
`PFIGate2ShellAcceptanceV1` evidence under `data/systemAudit/` and fails closed
when the browser, Streamlit health check, or shell iframe is unavailable.

The script verifies:

- Six workspace switches render Chinese business panels without page reload.
- Eight named UAT journeys open same-shell function detail panels and same-shell
  Chinese operation panels.
- Exhaustive feature-card replay opens every visible function card across all
  six primary entrances and fails if a card only switches workspace, opens a
  legacy page, opens a new page, or lacks a Chinese operation panel.
- Core function controls are buttons, not feature anchors to legacy pages.
- Parent URL never moves to `pfi_shell=0` or `pfi_legacy=1` during primary UAT.
- Visible surface has no retired identity terms, legacy placeholders, Python
  tracebacks, or English placeholder UI.
- WCAG structural proof covers named regions, live regions, labelled controls,
  focus styles, and 44px targets.
- `axe-core` runs when a local package is available; otherwise the script
  records an info line and still runs the local WCAG structural proof without
  network access.
- Performance budgets cover shell readiness, workspace switching, function
  opening, evidence drawer toggle, and command palette opening.

## Runtime Boundary

The script only starts local Streamlit if no healthy PFI OS service is found.
When it starts a service, it stops only that service at exit. It does not run
`finalAcceptanceCheck`, `ciSmoke`, full pytest, market refresh, broker
connections, real orders, payments, or holdings writes.

Generated JSON, screenshots, and logs are ignored by Git:

- `data/systemAudit/PFIGate2ShellAcceptance*.json`
- `data/systemAudit/PFIGate2ShellAcceptance*.png`
- `data/systemAudit/PFIGate2ShellAcceptance*.log`

## Verification Commands

```bash
python -m pytest tests/contract/test_pfi005_gate2_shell_acceptance.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/visual/test_pfi_web_shell_visual_baseline.py tests/test_scripts.py -q
zsh -n scripts/pfiGate2ShellAcceptance.sh
scripts/pfiGate2ShellAcceptance.sh --summary-json
scripts/pfiGate.sh target
git diff --check
```

Previous local evidence from 2026-06-20 before the rejected-delivery repair:

- Focused Web Shell/Gate2 contracts: 63 passed.
- Gate2 browser acceptance: `status=Pass`, `pass=126`, `fail=0`, `info=2`.
- Target gate with clean env Python: 46 passed, secret scan passed.
- Legacy identity regression: 2 passed.
- `git diff --check`: passed.

Current rejected-delivery repair evidence:

- Primary feature actions must keep the user inside PFI Web Shell and reveal
  `data-function-runner` with Chinese steps, status, and safety boundary.
- Direct links such as `?view=single` must render the PFI Shell and open the
  requested feature panel by default.
- Legacy Streamlit detail pages remain reachable only through explicit
  `pfi_legacy=1`, which is outside the default user acceptance path.
- Focused Web Shell/Gate2 contracts: 30 passed.
- Gate2 browser acceptance: `status=Pass`, `pass=228`, `fail=0`, `info=2`,
  screenshot
  `data/systemAudit/PFIGate2ShellAcceptance_20260620_071550.png`.
- UI visual browser acceptance: `status=Pass`, `pass=146`, `fail=0`, `info=0`,
  screenshot `data/systemAudit/UIVisualAcceptance_20260620_071622.png`.
- Target gate: 93 passed, secret scan passed.
- `zsh -n scripts/uiVisualAcceptance.sh scripts/pfiGate2ShellAcceptance.sh
  scripts/startPFIOS.sh`: passed.
- `git diff --check`: passed.

Current user-rejected redo evidence:

- All visible feature cards now resolve to same-shell function views, not
  passive workspace switches. The browser acceptance opened 46/46 visible
  function panels across 首页, 市场, 研究, 持仓, 策略实验室, 数据与系统.
- Function panels were rewritten to use Chinese user-facing wording for
  checks and boundaries; raw field names such as `bar_checksum`,
  `source_url`, `RunMetadata`, and `NeedsMoreEvidence` are not visible in the
  PFI Shell function-panel contract.
- Focused user-facing contracts: 38 passed.
- Gate2 browser acceptance: `status=Pass`, `pass=844`, `fail=0`, `info=2`,
  `all_feature_control_panels_opened=46`, screenshot
  `data/systemAudit/PFIGate2ShellAcceptance_20260620_073524.png`.
- UI visual browser acceptance: `status=Pass`, `pass=146`, `fail=0`,
  `info=0`, screenshot
  `data/systemAudit/UIVisualAcceptance_20260620_073602.png`.

## Stop Condition

Gate 2 is locally closed when the contract tests pass, the browser acceptance
JSON reports `status=Pass`, and `scripts/pfiGate.sh target` remains green. Gate
2 still needs replay during Gate 7 final packaging so the release artifact has
fresh runtime evidence.
