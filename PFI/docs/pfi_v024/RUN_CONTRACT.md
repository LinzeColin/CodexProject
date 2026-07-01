# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 7 / Phase 7.1 - 报告结构`。

不执行 Phase 7.2 页面展示，不执行 Phase 7.3 验收，不执行 Stage 7 whole-stage review，不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只建立报告中心的机器可读结构：

1. 固定净资产、现金、投资、消费、现金流、数据质量 6 类报告。
2. 固定每份报告的结论、公式、参数、数据范围、样本量、指标来源、置信度、缺口、异常项、复核入口和导出字段。
3. 使用 Stage 4 真实 read model status 作为输入，不补造任何财务指标。
4. 数据不足时只生成阻断报告和数据质量报告，不输出完整财务结论。
5. 生成 Phase 7.1 evidence pack，并停止等待下一轮 Phase 7.2 指令。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py
PFI/tests/test_v024_stage7_phase71_report_schema.py
PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_7/phase_7_1/*
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
PFI/reports/pfi_v024/stage_4/phase_4_2/read_model_status.json
PFI/reports/pfi_v024/stage_6/*
PFI/src/pfi_v02/stage_v023_reports.py
PFI/web/app/pages/reports.js
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_phase71_report_schema.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
python3 -m py_compile PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/report_quality_gate.json
python3 -m json.tool PFI/reports/pfi_v024/stage_7/phase_7_1/data_quality_report.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 7.2 or Phase 7.3.
- Do not perform Stage 7 whole-stage review.
- Do not push to GitHub main in this phase run.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
