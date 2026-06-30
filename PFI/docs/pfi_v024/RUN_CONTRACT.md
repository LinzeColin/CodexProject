# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 1 / Phase 1.3 - 验证。
不执行 Stage 1 whole-stage review 或后续 Stage。

## Goal

Run the Stage 1 validation closeout: record `node --check`, Stage 1 pytest
results, and the changed-files audit. This run may mark Stage 1 candidate
complete, but it must not claim Stage 1 whole-stage review, user acceptance, or
GitHub main upload.

## Allowed Files

```text
PFI/docs/pfi_v024/*
PFI/src/pfi_v02/stage_v024_pre_stage0_contract.py
PFI/src/pfi_v02/stage_v024_repair_contract.py
PFI/src/pfi_v02/stage_v024_stage1_shell_integrity.py
PFI/web/app/shell.js
PFI/web/app/version.js
PFI/tests/test_v024_pre_stage0_contract.py
PFI/tests/test_v024_stage0_phase01_contract.py
PFI/tests/test_v024_stage0_phase02_contract.py
PFI/tests/test_v024_stage0_phase03_contract.py
PFI/tests/test_v024_stage0_whole_review_contract.py
PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py
PFI/tests/test_v024_stage1_phase12_shell_repair.py
PFI/tests/test_v024_stage1_phase13_validation_closeout.py
PFI/reports/pfi_v024/pre_stage_0/*
PFI/reports/pfi_v024/stage_0/phase_0_1/*
PFI/reports/pfi_v024/stage_0/phase_0_2/*
PFI/reports/pfi_v024/stage_0/phase_0_3/*
PFI/reports/pfi_v024/stage_0/whole_stage_review/*
PFI/reports/pfi_v024/stage_1/phase_1_1/*
PFI/reports/pfi_v024/stage_1/phase_1_2/*
PFI/reports/pfi_v024/stage_1/phase_1_3/*
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
python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage1_shell_integrity.py
python3 -m py_compile PFI/tests/test_v024_pre_stage0_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_phase01_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_phase02_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_phase03_contract.py
python3 -m py_compile PFI/tests/test_v024_stage0_whole_review_contract.py
python3 -m py_compile PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py
python3 -m py_compile PFI/tests/test_v024_stage1_phase12_shell_repair.py
python3 -m py_compile PFI/tests/test_v024_stage1_phase13_validation_closeout.py
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase01_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase02_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_phase03_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage0_whole_review_contract.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage1_phase12_shell_repair.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_stage1_phase13_validation_closeout.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v024_pre_stage0_contract.py PFI/tests/test_v024_stage0_phase01_contract.py PFI/tests/test_v024_stage0_phase02_contract.py PFI/tests/test_v024_stage0_phase03_contract.py PFI/tests/test_v024_stage0_whole_review_contract.py PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py PFI/tests/test_v024_stage1_phase12_shell_repair.py PFI/tests/test_v024_stage1_phase13_validation_closeout.py -q
node --check PFI/web/app/version.js
python3 -m json.tool PFI/reports/pfi_v024/stage_1/phase_1_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_1/phase_1_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_1/phase_1_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/pre_stage_0/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/phase_0_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_0/whole_stage_review/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 1 whole-stage review in this run.
- Do not claim Stage 1 user acceptance or whole-stage completion.
- Do not push to GitHub main in this run.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not reconstruct or fabricate data.
- Do not rely on stale TaskPack GitHub audit claims without current checkout
  verification.
