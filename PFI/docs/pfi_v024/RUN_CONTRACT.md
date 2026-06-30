# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 3 GitHub main upload gate`。
不执行 Stage 4。

## Goal

Upload the reviewed Stage 3 package to GitHub `main`:

1. Confirm Stage 3 whole-stage review evidence is present.
2. Rebase local Stage 3 commits onto current `origin/main`.
3. Re-run Stage 3 navigation, browser, compatibility, JSON, and diff validations.
4. Push `HEAD:main`.
5. Fetch and verify `HEAD == origin/main == remote main`.

## Allowed Files

```text
PFI/web/app/routes.js
PFI/web/app/shell.js
PFI/src/pfi_v02/stage_v024_stage3_navigation.py
PFI/tests/test_v024_stage3_github_upload_contract.py
PFI/tests/test_v024_stage3_whole_review_contract.py
PFI/scripts/validate_v024_stage3_phase33_browser.js
PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md
PFI/docs/pfi_v024/STAGE3_WHOLE_STAGE_REVIEW.md
PFI/docs/pfi_v024/STAGE3_GITHUB_MAIN_UPLOAD.md
PFI/reports/pfi_v024/stage_3/github_main_upload/*
PFI/reports/pfi_v024/stage_3/whole_stage_review/*
PFI/reports/pfi_v024/stage_3/phase_3_3/browser_validation.json
PFI/reports/pfi_v024/stage_3/phase_3_3/legacy_routes_validation.json
PFI/reports/pfi_v024/stage_3/phase_3_3/screenshots/*
PFI/README.md
PFI/HANDOFF.md
PFI/CHANGELOG.md
PFI/功能清单.md
PFI/开发记录.md
PFI/模型参数文件.md
```

Read-only inspection allowed:

```text
PFI/web/index.html
PFI/web/app/navigation.js
PFI/src/pfi_os/app/streamlit_app.py
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_3/phase_3_1/*
PFI/reports/pfi_v024/stage_3/phase_3_2/*
PFI/reports/pfi_v024/stage_3/phase_3_3/*
PFI/tests/test_v024_stage3_phase31_navigation_contract.py
PFI/tests/test_v024_stage3_phase32_route_implementation.py
PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py
PFI/tests/test_v023_stage3_navigation_routes.py
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/routes.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/scripts/validate_v024_stage3_phase33_browser.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage3_navigation.py PFI/tests/test_v024_stage3_whole_review_contract.py PFI/tests/test_v024_stage3_github_upload_contract.py
NODE_PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.0/node_modules /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node PFI/scripts/validate_v024_stage3_phase33_browser.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_github_upload_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_pre_stage0_contract.py PFI/tests/test_v024_stage0_phase01_contract.py PFI/tests/test_v024_stage0_phase02_contract.py PFI/tests/test_v024_stage0_phase03_contract.py PFI/tests/test_v024_stage0_whole_review_contract.py PFI/tests/test_v024_stage1_phase11_shell_diagnosis.py PFI/tests/test_v024_stage1_phase12_shell_repair.py PFI/tests/test_v024_stage1_phase13_validation_closeout.py PFI/tests/test_v024_stage1_whole_review_contract.py PFI/tests/test_v024_stage2_phase21_entry_mapping.py PFI/tests/test_v024_stage2_phase22_version_link.py PFI/tests/test_v024_stage2_phase23_real_entry_validation.py PFI/tests/test_v024_stage2_whole_review_contract.py PFI/tests/test_v024_stage3_phase31_navigation_contract.py PFI/tests/test_v024_stage3_phase32_route_implementation.py PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py PFI/tests/test_v024_stage3_whole_review_contract.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_3/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_3/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_3/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_3/phase_3_3/legacy_routes_validation.json
git diff --check -- PFI
git push origin HEAD:main
git ls-remote origin refs/heads/main
```

## Explicit Non-Goals

- Do not enter Stage 4 in this run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C source or Info.plist.
- Do not change business financial UI data logic, metrics, formulas, or user data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
- Do not claim upload complete without terminal remote verification.
