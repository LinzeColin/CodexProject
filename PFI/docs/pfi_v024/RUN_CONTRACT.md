# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 Stage 1 whole-stage review - 复审并解决暴露问题。
不执行 Stage 2，不执行 GitHub main upload。

## Goal

Review the complete Stage 1 shell integrity work after Phase 1.1, Phase 1.2,
and Phase 1.3 candidate pass. The review must add a whole-stage review
contract, evidence pack, and status updates. It may mark Stage 1 complete at
local review level, but it must not claim Stage 2 entry or GitHub main upload.

## Allowed Files

```text
PFI/docs/pfi_v024/*
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
PFI/tests/test_v024_stage1_whole_review_contract.py
PFI/reports/pfi_v024/stage_1/phase_1_1/*
PFI/reports/pfi_v024/stage_1/phase_1_2/*
PFI/reports/pfi_v024/stage_1/phase_1_3/*
PFI/reports/pfi_v024/stage_1/whole_stage_review/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

## Validation

```bash
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/version.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage1_shell_integrity.py PFI/tests/test_v024_stage1_whole_review_contract.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage1_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py PFI/tests/test_v024_stage1_phase12_shell_repair.py PFI/tests/test_v024_stage1_phase13_validation_closeout.py PFI/tests/test_v024_stage1_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_pre_stage0_contract.py PFI/tests/test_v024_stage0_phase01_contract.py PFI/tests/test_v024_stage0_phase02_contract.py PFI/tests/test_v024_stage0_phase03_contract.py PFI/tests/test_v024_stage0_whole_review_contract.py PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py PFI/tests/test_v024_stage1_phase12_shell_repair.py PFI/tests/test_v024_stage1_phase13_validation_closeout.py PFI/tests/test_v024_stage1_whole_review_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_1/whole_stage_review/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 2 in this run.
- Do not claim Stage 2 entry consistency.
- Do not push to GitHub main in this run.
- Do not modify business UI, app bundle, runtime launcher, or data logic.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not reconstruct or fabricate data.
- Do not rely on README/docs declarations without evidence and test output.
