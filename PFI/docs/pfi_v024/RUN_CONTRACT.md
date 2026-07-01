# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 5 GitHub main upload gate`。

不执行 Stage 6，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

将已经完成整阶段复审的 Stage 5 package 上传到 GitHub `main`，并用远端事实验证：

1. Stage 5 Phase 5.1、Phase 5.2、Phase 5.3 均为 candidate pass。
2. Stage 5 whole-stage review 为 pass，复审发现问题均已 fixed。
3. 上传前重新验证 Stage 5 upload contract、whole-stage review、Stage 5 phase regression 和 Stage 3/4 adjacent regression。
4. 上传后必须用 `git ls-remote origin refs/heads/main`、`git rev-parse HEAD`、`git rev-parse origin/main` 证明 `HEAD == origin/main == remote main`。
5. 本轮只关闭 Stage 5 upload gate，不自动进入 Stage 6。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage5_experience.py
PFI/tests/test_v024_stage5_github_upload_contract.py
PFI/docs/pfi_v024/STAGE5_GITHUB_MAIN_UPLOAD.md
PFI/reports/pfi_v024/stage_5/github_main_upload/*
PFI/docs/pfi_v024/RUN_CONTRACT.md
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
PFI/PRODUCT.md
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_5/phase_5_1/*
PFI/reports/pfi_v024/stage_5/phase_5_2/*
PFI/reports/pfi_v024/stage_5/phase_5_3/*
PFI/reports/pfi_v024/stage_5/whole_stage_review/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/scripts/validate_v024_stage5_whole_review_browser.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_v02/stage_v024_stage5_experience.py PFI/src/pfi_os/app/streamlit_app.py PFI/tests/test_v024_stage5_github_upload_contract.py PFI/tests/test_v024_stage5_whole_review_contract.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_github_upload_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_github_upload_contract.py PFI/tests/test_v024_stage5_whole_review_contract.py PFI/tests/test_v024_stage5_phase51_home_rebuild.py PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py PFI/tests/test_v024_stage5_phase53_interaction_states.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_phase32_route_implementation.py PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase43_acceptance.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_5/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/whole_stage_review/browser_validation.json
git diff --check -- PFI
git push origin HEAD:main
git fetch origin main
git ls-remote origin refs/heads/main
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count HEAD...origin/main
```

## Explicit Non-Goals

- Do not enter Stage 6.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
