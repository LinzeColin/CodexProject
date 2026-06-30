# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 3 / Phase 3.3 - 导航验收`。
不执行 Stage 3 whole-stage review 或 GitHub main upload。

## Goal

Validate the Stage 3 navigation contract in a real browser:

1. Desktop and mobile DOM expose exactly 10 formal first-level entries.
2. `市场与研究` remains the 9th formal first-level entry.
3. v0.1 labels `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` resolve as aliases or redirects, not peer primary entries.
4. Browser click navigation works through the route table.
5. Browser back/forward and direct URL alias validation pass with screenshots and JSON evidence.

## Allowed Files

```text
PFI/web/app/routes.js
PFI/web/app/shell.js
PFI/src/pfi_v02/stage_v024_stage3_navigation.py
PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py
PFI/scripts/validate_v024_stage3_phase33_browser.js
PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md
PFI/reports/pfi_v024/stage_3/phase_3_3/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

Read-only inspection allowed:

```text
PFI/web/index.html
PFI/web/app/navigation.js
PFI/src/pfi_os/app/streamlit_app.py
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_3/phase_3_1/*
PFI/reports/pfi_v024/stage_3/phase_3_2/*
PFI/tests/test_v024_stage3_phase31_navigation_contract.py
PFI/tests/test_v024_stage3_phase32_route_implementation.py
PFI/tests/test_v023_stage3_navigation_routes.py
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/routes.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/scripts/validate_v024_stage3_phase33_browser.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage3_navigation.py PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py
NODE_PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.0/node_modules /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node PFI/scripts/validate_v024_stage3_phase33_browser.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_3/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_3/legacy_routes_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not run Stage 3 whole-stage review in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not change business financial UI data logic, metrics, formulas, or user data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
