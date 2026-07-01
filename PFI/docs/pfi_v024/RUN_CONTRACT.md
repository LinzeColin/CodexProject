# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 7 GitHub main upload gate`。

不进入 Stage 8，不重装 app bundle，不修改 launcher C/Info.plist，
不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只上传已经完成整阶段复审的 Stage 7 package：

1. 确认 Stage 7 Phase 7.1、7.2、7.3 均为 candidate pass。
2. 确认 Stage 7 whole-stage review 为 pass，且 3 项复审发现均已 fixed。
3. 生成 Stage 7 GitHub main upload gate contract、文档和 evidence pack。
4. 上传前重新运行 Stage 7 upload、whole-review、phase regression、Stage 6 adjacent regression、browser validation、syntax、JSON 和 diff checks。
5. `git push origin HEAD:main` 后用 terminal 重新验证 `HEAD == origin/main == remote main`。
6. 停止在 Stage 7 upload complete，不自动进入 Stage 8。

Stage 7 package scope:

- `Stage 7 / Phase 7.1 - 报告结构`
- `Stage 7 / Phase 7.2 - 页面展示`
- `Stage 7 / Phase 7.3 - 验收`
- `Stage 7 whole-stage review - 复审并解决暴露问题`

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py
PFI/tests/test_v024_stage7_github_upload_contract.py
PFI/docs/pfi_v024/STAGE7_GITHUB_MAIN_UPLOAD.md
PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_7/github_main_upload/*
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
PFI/reports/pfi_v024/stage_7/phase_7_1/*
PFI/reports/pfi_v024/stage_7/phase_7_2/*
PFI/reports/pfi_v024/stage_7/phase_7_3/*
PFI/reports/pfi_v024/stage_7/whole_stage_review/*
PFI/reports/pfi_v024/stage_6/*
PFI/web/app/pages/reports.js
PFI/web/app/shell.js
PFI/src/pfi_os/app/streamlit_app.py
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
git fetch origin main
git rev-list --left-right --count HEAD...origin/main
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_github_upload_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_whole_review_contract.py PFI/tests/test_v024_stage7_phase71_report_schema.py PFI/tests/test_v024_stage7_phase72_report_page_display.py PFI/tests/test_v024_stage7_phase73_report_acceptance.py -q
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/Documents/Codex/CodexProject/EEI/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/pages/reports.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py PFI/src/pfi_os/app/streamlit_app.py
python3 -m json.tool PFI/reports/pfi_v024/stage_7/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/report_acceptance_gate.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/report_center_view_model.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/page_display_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_quality_gate.json
test -s PFI/reports/pfi_v024/stage_7/phase_7_3/formula_visibility.png
git diff --check -- PFI
git push origin HEAD:main
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
git ls-remote origin refs/heads/main
```

## Explicit Non-Goals

- Do not start Stage 8.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
