# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 3 / Phase 3.2 - 路由实现`。
不执行 Phase 3.3、Stage 3 whole-stage review 或 GitHub main upload。

## Goal

Implement the route layer for the Stage 3 navigation contract:

1. All 10 official first-level entries resolve as primary routes.
2. Owned second-level routes resolve to their workspace and primary route.
3. v0.1 labels `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` redirect to owned v0.2.4 routes.
4. Runtime shell uses the route table before fallback parsing.
5. Hash/history/popstate handling is declared for Phase 3.3 browser validation.

## Allowed Files

```text
PFI/web/app/routes.js
PFI/web/app/shell.js
PFI/src/pfi_v02/stage_v024_stage3_navigation.py
PFI/tests/test_v024_stage3_phase32_route_implementation.py
PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md
PFI/reports/pfi_v024/stage_3/phase_3_2/*
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
PFI/tests/test_v023_stage3_navigation_routes.py
PFI/tests/test_v024_stage3_phase31_navigation_contract.py
```

## Validation

```bash
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/routes.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage3_navigation.py PFI/tests/test_v024_stage3_phase32_route_implementation.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_phase32_route_implementation.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_2/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not perform Phase 3.3 real browser back/forward/direct URL validation in this run.
- Do not run Stage 3 whole-stage review in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not change business financial UI data logic, metrics, formulas, or user data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
