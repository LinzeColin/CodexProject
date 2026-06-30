# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Pre Stage 0 / Phase P0.0 - context convergence.
不执行 Stage 0，不执行后续 Stage。

## Goal

Parse the user-provided `v0.2.3-repair` roadmap/taskpack, map it to the
v0.2.4 target, verify current GitHub `main`, and create a durable pre-stage
baseline for the next v0.2.4 Stage 0 run.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
PFI/tests/test_v024_pre_stage0_contract.py
PFI/reports/pfi_v024/pre_stage_0/*
PFI/README.md
PFI/HANDOFF.md
```

## Validation

```bash
node --check PFI/web/app/shell.js
python3 -m py_compile PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
python3 -m py_compile PFI/tests/test_v024_pre_stage0_contract.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/pre_stage_0/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute v0.2.4 Stage 0.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not reconstruct or fabricate data.
- Do not rely on stale TaskPack GitHub audit claims without current checkout
  verification.

