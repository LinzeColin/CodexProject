# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 0 / Phase 0.3 - Stage 0 测试与证据。
不执行 Stage 0 whole-stage review、Stage 1 或后续 Stage。

## Goal

Verify the Stage 0 repair contract with focused tests and a phase-bounded
evidence pack. Phase 0.1 and Phase 0.2 are already candidate pass; this run
only proves the 10-entry nav contract, `市场与研究` top-level status, the
no-mock financial data rule, and Phase 0.3 evidence completeness.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
PFI/src/pfi_v02/stage_v024_repair_contract.py
PFI/tests/test_v024_pre_stage0_contract.py
PFI/tests/test_v024_stage0_phase01_contract.py
PFI/tests/test_v024_stage0_phase02_contract.py
PFI/tests/test_v024_stage0_phase03_contract.py
PFI/reports/pfi_v024/pre_stage_0/*
PFI/reports/pfi_v024/stage_0/phase_0_1/*
PFI/reports/pfi_v024/stage_0/phase_0_2/*
PFI/reports/pfi_v024/stage_0/phase_0_3/*
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
python3 -m py_compile PFI/tests/test_v024_stage0_phase02_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_phase03_contract.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase01_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase02_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase03_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/pre_stage_0/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_3/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 0 whole-stage review.
- Do not claim Stage 0 reviewed or user accepted.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not reconstruct or fabricate data.
- Do not rely on stale TaskPack GitHub audit claims without current checkout
  verification.
