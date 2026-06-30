# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 0 / Phase 0.1 - 需求合同冻结。
不执行 Phase 0.2、Phase 0.3、Stage 0 whole-stage review 或后续 Stage。

## Goal

Freeze the v0.2.4 repair positioning, 10-entry product contract, real-data
trust contract, and one-phase-per-run rule while preserving the source package
mapping from `v0.2.3-repair`.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
PFI/src/pfi_v02/stage_v024_repair_contract.py
PFI/tests/test_v024_pre_stage0_contract.py
PFI/tests/test_v024_stage0_phase01_contract.py
PFI/reports/pfi_v024/pre_stage_0/*
PFI/reports/pfi_v024/stage_0/phase_0_1/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

## Validation

```bash
node --check PFI/web/app/shell.js
python3 -m py_compile PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
python3 -m py_compile PFI/src/pfi_v02/stage_v024_repair_contract.py
python3 -m py_compile PFI/tests/test_v024_pre_stage0_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_phase01_contract.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase01_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/pre_stage_0/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_1/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 0.2 or Phase 0.3.
- Do not claim Stage 0 complete.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not reconstruct or fabricate data.
- Do not rely on stale TaskPack GitHub audit claims without current checkout
  verification.
