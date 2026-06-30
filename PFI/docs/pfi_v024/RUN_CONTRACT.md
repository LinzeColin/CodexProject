# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 2 / Phase 2.2 - 版本链路实现。
不执行 Phase 2.3、Stage 2 whole-stage review 或 GitHub main upload。

## Goal

Implement the visible and machine-readable version chain defined in Phase 2.1:
repair label, build id, bundle version, bundle hash, UI contract version, and
entry audit read model. This phase may mark Phase 2.2 candidate pass, but it
must not claim real app/browser validation is complete.

## Allowed Files

```text
PFI/StartPFI.command
PFI/docs/pfi_v024/*
PFI/src/pfi_os/app/streamlit_app.py
PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py
PFI/scripts/startPFI.sh
PFI/tests/test_pfi_app_entry_version_contract.py
PFI/tests/test_v023_stage1_app_entry_bundle_contract.py
PFI/tests/test_v024_stage1_whole_review_contract.py
PFI/tests/test_v024_stage2_phase22_version_link.py
PFI/reports/pfi_v024/stage_2/phase_2_2/*
PFI/web/index.html
PFI/web/styles/tokens.css
PFI/web/app/shell.js
PFI/web/app/version.js
PFI/web/app/entry_audit.js
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
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py PFI/tests/test_v024_stage2_phase22_version_link.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage2_phase22_version_link.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_2/phase_2_2/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 2.3 real app/browser validation in this run.
- Do not claim app and localhost real-browser consistency is fully validated.
- Do not reinstall or mutate app bundles.
- Do not modify app launcher C source or Info.plist.
- Do not change business financial UI flows or data logic.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not push to GitHub main in this run.
