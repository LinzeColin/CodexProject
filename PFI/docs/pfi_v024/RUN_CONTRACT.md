# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 4 / Phase 4.1 - 状态机定义`。
不执行 Phase 4.2、Phase 4.3、Stage 4 whole-stage review 或 GitHub main upload。

## Goal

Freeze the Stage 4 data-state contract so core financial metrics can no longer
collapse unloaded, failed, stale, or filtered states into an unexplained
`CNY 0.00`:

1. Define the core metric state enum.
2. Define the required metric state schema.
3. Define Chinese blocking reasons for every non-ready state.
4. Lock the no-fake-zero rule and the confirmed-zero evidence chain.

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage4_data_state.py
PFI/web/app/data_state.js
PFI/tests/test_v024_stage4_phase41_data_state_contract.py
PFI/tests/test_v024_stage4_no_mock_financial_data.py
PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md
PFI/reports/pfi_v024/stage_4/phase_4_1/*
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
PFI/reports/pfi_v024/stage_3/*
PFI/src/pfi_v02/stage_v023_data_state.py
PFI/web/app/dataStatus.js
PFI/tests/test_v023_stage2_data_state_machine.py
PFI/tests/test_v023_no_mock_financial_data.py
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage4_data_state.py PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_1/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not enter Stage 4 Phase 4.2 read model 挂链 in this run.
- Do not enter Stage 4 Phase 4.3 验收 in this run.
- Do not run Stage 4 whole-stage review in this run.
- Do not push or claim GitHub main upload in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not read, rewrite, clean, delete, or synthesize user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
