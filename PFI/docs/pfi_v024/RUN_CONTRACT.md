# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 4 GitHub main upload gate`。
不执行 Stage 5。

## Goal

Upload the reviewed Stage 4 data-state and read-model recovery package to
GitHub main after rebasing and re-validating the current checkout:

1. Stage 4 Phase 4.1/4.2/4.3 must remain candidate pass.
2. Stage 4 whole-stage review must remain pass.
3. Current local `MetaDatabase/PFI` state must remain represented without fake financial data.
4. Upload must happen only after current `origin/main` is fetched/rebased.
5. Final proof must come from terminal verification that `HEAD == origin/main == remote main`.

## Allowed Files

```text
PFI/docs/pfi_v024/STAGE4_GITHUB_MAIN_UPLOAD.md
PFI/tests/test_v024_stage4_github_upload_contract.py
PFI/src/pfi_v02/stage_v024_stage4_data_state.py
PFI/web/app/data_state.js
PFI/web/app/shell.js
PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md
PFI/reports/pfi_v024/stage_4/github_main_upload/*
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
PFI/reports/pfi_v024/stage_4/phase_4_3/*
PFI/reports/pfi_v024/stage_4/whole_stage_review/*
PFI/src/pfi_os/application/read_model_status.py
MetaDatabase/PFI/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/data_state.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/tests/test_v024_stage4_github_upload_contract.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage4_github_upload_contract.py PFI/tests/test_v024_stage4_whole_review_contract.py PFI/tests/test_v024_stage4_phase43_acceptance.py PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase41_data_state_contract.py PFI/tests/test_v024_stage4_no_mock_financial_data.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_4/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_4/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_4/phase_4_3/browser_validation.json
git diff --check -- PFI
git push origin HEAD:main
git ls-remote origin refs/heads/main
```

## Explicit Non-Goals

- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not start Stage 5 in this run.
