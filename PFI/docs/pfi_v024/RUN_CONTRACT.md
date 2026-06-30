# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 0 whole-stage review - 复审并解决暴露问题。
不执行 Stage 1 或后续 Stage。

## Goal

Review Stage 0 after Phase 0.1, Phase 0.2, and Phase 0.3 are candidate pass.
Fix only Stage 0-scoped review findings, produce the whole-stage review
evidence pack, and keep Stage 1 blocked until user acceptance or explicit
instruction.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
PFI/src/pfi_v02/stage_v024_repair_contract.py
PFI/tests/test_v024_pre_stage0_contract.py
PFI/tests/test_v024_stage0_phase01_contract.py
PFI/tests/test_v024_stage0_phase02_contract.py
PFI/tests/test_v024_stage0_phase03_contract.py
PFI/tests/test_v024_stage0_whole_review_contract.py
PFI/reports/pfi_v024/pre_stage_0/*
PFI/reports/pfi_v024/stage_0/phase_0_1/*
PFI/reports/pfi_v024/stage_0/phase_0_2/*
PFI/reports/pfi_v024/stage_0/phase_0_3/*
PFI/reports/pfi_v024/stage_0/whole_stage_review/*
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
python3 -m py_compile PFI/tests/test_v024_stage0_whole_review_contract.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase01_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase02_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase03_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_whole_review_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py PFI/tests/test_v024_stage0_phase01_contract.py PFI/tests/test_v024_stage0_phase02_contract.py PFI/tests/test_v024_stage0_phase03_contract.py PFI/tests/test_v024_stage0_whole_review_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/pre_stage_0/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/whole_stage_review/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 1.
- Do not claim Stage 1 user acceptance or implementation.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not reconstruct or fabricate data.
- Do not rely on stale TaskPack GitHub audit claims without current checkout
  verification.
