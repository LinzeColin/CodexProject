# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 3 / Phase 3.1 - 导航合同`。
不执行 Phase 3.2、Phase 3.3、Stage 3 whole-stage review 或 GitHub main upload。

## Goal

Freeze the Stage 3 navigation contract for the repair package:

1. Official first-level navigation has exactly 10 entries.
2. `市场与研究` is a formal first-level entry at index 9.
3. v0.1 labels `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` remain accessible only as secondary/alias/command paths.
4. The page does not expose 16 peer first-level entries in sidebar, bottom navigation, or no-js fallback.
5. Active-state rules are declared before Phase 3.2 route implementation.

## Allowed Files

```text
PFI/web/index.html
PFI/web/app/navigation.js
PFI/web/app/routes.js
PFI/web/app/shell.js
PFI/src/pfi_os/app/streamlit_app.py
PFI/src/pfi_v02/stage_v024_stage3_navigation.py
PFI/tests/test_v024_stage3_phase31_navigation_contract.py
PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md
PFI/reports/pfi_v024/stage_3/phase_3_1/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

Read-only inspection allowed:

```text
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_2/*
PFI/tests/test_v023_stage3_navigation_routes.py
PFI/tests/test_v024_stage2_*.py
PFI/StartPFI.command
PFI/scripts/startPFI.sh
```

## Validation

```bash
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/navigation.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/routes.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage3_navigation.py PFI/tests/test_v024_stage3_phase31_navigation_contract.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_phase31_navigation_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_1/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not implement Phase 3.2 route mutation, redirect, or history behavior in this run.
- Do not perform Phase 3.3 browser back/forward/direct URL validation in this run.
- Do not run Stage 3 whole-stage review in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not change business financial UI data logic, metrics, formulas, or user data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
