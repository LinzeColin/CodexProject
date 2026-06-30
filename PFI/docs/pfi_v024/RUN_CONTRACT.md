# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 2 / Phase 2.1 - 入口链路映射。
不执行 Phase 2.2、Phase 2.3、Stage 2 whole-stage review 或 GitHub main upload。

## Goal

Map the app, localhost, Streamlit, static HTML, shell runtime, and version
surfaces that must become consistent in Stage 2. Record old UI signatures and
define the build/hash display locations for Phase 2.2. This phase may mark
Phase 2.1 candidate pass, but it must not claim entry consistency is fixed.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py
PFI/tests/test_v024_stage2_phase21_entry_mapping.py
PFI/reports/pfi_v024/stage_2/phase_2_1/*
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
PFI/web/app/shell.js
PFI/web/app/version.js
PFI/src/pfi_os/app/streamlit_app.py
PFI/scripts/startPFI.sh
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
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py PFI/tests/test_v024_stage2_phase21_entry_mapping.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage2_phase21_entry_mapping.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_2/phase_2_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_2/phase_2_1/old_ui_signatures.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not implement Phase 2.2 version-link changes in this run.
- Do not execute Phase 2.3 real app/browser validation in this run.
- Do not claim app and localhost entry consistency is fixed.
- Do not modify `PFI/web/index.html`, `PFI/web/app/shell.js`, `PFI/web/app/version.js`, app bundles, launchers, or data logic.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
