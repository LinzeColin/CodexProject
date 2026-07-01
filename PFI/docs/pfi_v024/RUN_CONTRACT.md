# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 6 GitHub main upload gate`。

不执行 Stage 7，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只上传已完成整阶段复审的 Stage 6 package：

1. 确认 Stage 6 Phase 6.1、6.2、6.3 和 whole-stage review 均通过。
2. 确认当前分支已 rebase 到最新 `origin/main`，且远端漂移未触碰 `PFI/`。
3. 运行 Stage 6 upload gate、whole review、phase regression、Stage 5 adjacent regression、browser validation、syntax、JSON 和 diff checks。
4. `git push origin HEAD:main`。
5. 上传后用 `git ls-remote origin refs/heads/main` 和 fresh fetch 证明 `HEAD == origin/main == remote main`。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage6_experience.py
PFI/tests/test_v024_stage6_github_upload_contract.py
PFI/docs/pfi_v024/STAGE6_GITHUB_MAIN_UPLOAD.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_6/github_main_upload/*
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
PFI/reports/pfi_v024/stage_6/*
PFI/reports/pfi_v024/stage_5/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.1/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage6_whole_review_browser.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_github_upload_contract.py PFI/tests/test_v024_stage6_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_phase51_home_rebuild.py PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py PFI/tests/test_v024_stage5_phase53_interaction_states.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage6_whole_review_browser.js
python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage6_experience.py
python3 -m json.tool PFI/reports/pfi_v024/stage_6/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_6/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_6/whole_stage_review/browser_validation.json
git diff --check -- PFI
git push origin HEAD:main
git ls-remote origin refs/heads/main
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
```

## Explicit Non-Goals

- Do not execute Stage 7.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
