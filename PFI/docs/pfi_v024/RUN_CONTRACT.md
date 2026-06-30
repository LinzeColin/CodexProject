# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 4 / Phase 4.2 - read model 挂链`。
不执行 Phase 4.3、Stage 4 whole-stage review 或 GitHub main upload。

## Goal

Wire the Phase 4.1 metric data-state contract into one shared read model status
that Home, accounts, investment, consumption, and reports can read consistently:

1. Read current local real data state from `MetaDatabase/PFI` without mutating user data.
2. Produce `source/status/as_of/record_count` machine JSON.
3. Expose the shared read model through `/api/read-model-status` and embedded app JSON.
4. Make core cards read status objects instead of falling back to unexplained zero.

## Allowed Files

```text
PFI/src/pfi_os/application/read_model_status.py
PFI/src/pfi_v02/stage_v021_runtime_api.py
PFI/web/app/data_state.js
PFI/web/app/shell.js
PFI/web/index.html
PFI/src/pfi_os/app/streamlit_app.py
PFI/tests/test_v024_stage4_phase42_read_model_link.py
PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md
PFI/reports/pfi_v024/stage_4/phase_4_2/*
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
PFI/reports/pfi_v024/stage_4/phase_4_1/*
PFI/src/pfi_v02/stage_v024_stage4_data_state.py
PFI/src/pfi_v02/stage_v023_core_metrics.py
PFI/src/pfi_v02/stage_v023_read_model.py
MetaDatabase/PFI/*
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_os/application/read_model_status.py PFI/src/pfi_v02/stage_v021_runtime_api.py PFI/src/pfi_os/app/streamlit_app.py PFI/tests/test_v024_stage4_phase42_read_model_link.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_2/read_model_status.json
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_2/page_metric_states.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not enter Stage 4 Phase 4.3 验收 in this run.
- Do not run Stage 4 whole-stage review in this run.
- Do not push or claim GitHub main upload in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
