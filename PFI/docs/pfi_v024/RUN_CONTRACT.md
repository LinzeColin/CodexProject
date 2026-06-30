# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 4 / Phase 4.3 - 验收`。
不执行 Stage 4 whole-stage review 或 GitHub main upload。

## Goal

Validate the Stage 4 data-state and read-model recovery contract with tests and
browser evidence:

1. Blocked or missing real data must not render as `CNY 0.00`.
2. `confirmed_zero` must require source, as-of time, record count, formula, and confidence evidence.
3. Current local `MetaDatabase/PFI` state must be represented in browser evidence.
4. Frontend null `record_count` / `confidence` must remain unknown, not become `0`.

## Allowed Files

```text
PFI/scripts/validate_v024_stage4_phase43_chrome.py
PFI/tests/test_v024_stage4_phase43_acceptance.py
PFI/web/app/data_state.js
PFI/web/app/shell.js
PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md
PFI/reports/pfi_v024/stage_4/phase_4_3/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

Read-only inspection allowed:

```text
AGENTS.md
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_4/phase_4_1/*
PFI/reports/pfi_v024/stage_4/phase_4_2/*
PFI/src/pfi_v02/stage_v024_stage4_data_state.py
PFI/src/pfi_os/application/read_model_status.py
MetaDatabase/PFI/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/scripts/validate_v024_stage4_phase43_chrome.py PFI/tests/test_v024_stage4_phase43_acceptance.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -B PFI/scripts/validate_v024_stage4_phase43_chrome.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage4_phase43_acceptance.py PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_3/browser_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not run Stage 4 whole-stage review in this run.
- Do not push or claim GitHub main upload in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
