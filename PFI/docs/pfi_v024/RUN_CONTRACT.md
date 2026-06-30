# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 2 whole-stage review - 复审并解决暴露问题。
不执行 Stage 3 或 GitHub main upload。

## Goal

Review Phase 2.1, Phase 2.2, and Phase 2.3 together against the Stage 2
app/localhost entry-consistency acceptance criteria. Fix review findings within
the Stage 2 boundary, refresh evidence if it is stale, and close Stage 2
locally without starting Stage 3 or uploading GitHub main.

## Allowed Files

```text
PFI/StartPFI.command
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py
PFI/scripts/startPFI.sh
PFI/scripts/validate_v024_stage2_phase23_entry.js
PFI/tests/test_v024_stage2_phase23_real_entry_validation.py
PFI/tests/test_v024_stage2_whole_review_contract.py
PFI/reports/pfi_v024/stage_2/phase_2_3/*
PFI/reports/pfi_v024/stage_2/whole_stage_review/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

Read-only inspection allowed:

```text
PFI/scripts/installPFIEntryApps.sh
PFI/macos/PFI_launcher.c
PFI/macos/PFI.app/Contents/Info.plist
/Applications/PFI.app
~/Downloads/PFI.app
~/Desktop/PFI.app
```

## Validation

```bash
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/version.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/entry_audit.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/scripts/validate_v024_stage2_phase23_entry.js
zsh -n PFI/StartPFI.command
zsh -n PFI/scripts/startPFI.sh
PLAYWRIGHT_CORE_PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.61.0/node_modules/playwright-core CHROME_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node PFI/scripts/validate_v024_stage2_phase23_entry.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py PFI/tests/test_v024_stage2_phase23_real_entry_validation.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/tests/test_v024_stage2_whole_review_contract.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage2_phase23_real_entry_validation.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage2_whole_review_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_2/phase_2_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_2/phase_2_3/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_2/whole_stage_review/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not start Stage 3 navigation repair in this run.
- Do not reinstall or mutate app bundles.
- Do not modify app launcher C source or Info.plist.
- Do not change business financial UI flows or data logic.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
