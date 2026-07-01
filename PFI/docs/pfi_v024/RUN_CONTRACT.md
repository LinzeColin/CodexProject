# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 6 / Phase 6.1 - 设计系统`。

不执行 Phase 6.2 动效反馈，不执行 Phase 6.3 触感与设置隔离，不执行 Stage 6 whole-stage review，不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只完成 Stage 6 Phase 6.1：

1. T6.1.1 建立默认浅色设计 token。
2. T6.1.2 建立状态色系统。
3. T6.1.3 让卡片、表格、图表槽共享设计系统。
4. T6.1.4 补齐响应式布局，不引入桌面手机预览框。

## Allowed Files

```text
PFI/web/index.html
PFI/web/styles.css
PFI/tests/test_v024_stage6_phase61_design_system.py
PFI/docs/pfi_v024/STAGE6_DESIGN_SYSTEM.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_6/phase_6_1/*
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
PFI/reports/pfi_v024/stage_5/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
python3 -m json.tool PFI/reports/pfi_v024/stage_6/phase_6_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_6/phase_6_1/design_token_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 6.2 motion feedback.
- Do not execute Phase 6.3 haptics and settings isolation.
- Do not execute Stage 6 whole-stage review.
- Do not upload to GitHub main.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
