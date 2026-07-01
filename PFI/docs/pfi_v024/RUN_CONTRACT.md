# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 7 / Phase 7.3 - 验收`。

不执行 Stage 7 whole-stage review，不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只验收 Stage 7 Phase 7.1/7.2 的报告中心交付：

1. 证明报告中心页面展示净资产、现金、投资、消费、现金流、数据质量 6 份报告。
2. 证明每份报告的结论、公式、参数、样本量、数据范围、置信度、缺口和复核入口可见。
3. 证明数据不足时只生成数据质量报告与阻断状态，不输出完整财务结论。
4. 证明报告不会退化成单段 AI 总结。
5. 生成 Phase 7.3 evidence pack，并停止等待下一轮 whole-stage review 指令。

## Allowed Files

```text
PFI/web/app/pages/reports.js
PFI/web/app/shell.js
PFI/web/index.html
PFI/src/pfi_os/app/streamlit_app.py
PFI/tests/test_v024_stage7_phase72_report_page_display.py
PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_7/phase_7_3/*
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
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/Documents/Codex/CodexProject/EEI/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/pages/reports.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_os/app/streamlit_app.py
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

- Do not perform Stage 7 whole-stage review.
- Do not push to GitHub main in this phase run.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
