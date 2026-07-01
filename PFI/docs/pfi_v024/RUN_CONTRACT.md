# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 7 whole-stage review - 复审并解决暴露问题`。

不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只复审 Stage 7 Phase 7.1、7.2、7.3 的报告中心交付：

1. 复审 `Stage 7 / Phase 7.1 - 报告结构` 的 schema、6 类报告、阻断规则和质量门禁。
2. 复审 `Stage 7 / Phase 7.2 - 页面展示` 的报告中心 view model 与公式/参数/样本量/范围可见性。
3. 复审 `Stage 7 / Phase 7.3 - 验收` 的数据不足报告测试、反单段 AI 文本测试和截图 evidence。
4. 记录并修复 whole-stage review 暴露的问题。
5. 生成 whole-stage review evidence pack，并停止等待下一轮 GitHub main upload gate 指令。

## Allowed Files

```text
PFI/web/app/pages/reports.js
PFI/tests/test_v024_stage7_whole_review_contract.py
PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md
PFI/docs/pfi_v024/STAGE7_WHOLE_STAGE_REVIEW.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_7/whole_stage_review/*
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
PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json
PFI/reports/pfi_v024/stage_7/phase_7_2/*
PFI/reports/pfi_v024/stage_7/phase_7_3/*
PFI/reports/pfi_v024/stage_4/phase_4_2/read_model_status.json
PFI/web/app/pages/reports.js
PFI/web/app/shell.js
PFI/web/index.html
PFI/src/pfi_os/app/streamlit_app.py
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_phase72_report_page_display.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_phase71_report_schema.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_phase73_report_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_whole_review_contract.py -q
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/Documents/Codex/CodexProject/EEI/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/pages/reports.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_os/app/streamlit_app.py
python3 -m json.tool PFI/reports/pfi_v024/stage_7/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/report_acceptance_gate.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_3/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/report_center_view_model.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_2/page_display_validation.json
test -s PFI/reports/pfi_v024/stage_7/phase_7_3/formula_visibility.png
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not push to GitHub main in this phase run.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
