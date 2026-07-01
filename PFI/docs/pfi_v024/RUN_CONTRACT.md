# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 8 whole-stage review - 复审并解决暴露问题`。

历史前置已完成：

- `Stage 8 / Phase 8.2 - 截图验收`。历史 Phase 8.2 当轮停止条件为：不执行 Phase 8.3。
- `Stage 8 / Phase 8.3 - 人工验收`。历史 Phase 8.3 当轮停止条件为：不执行 Stage 8 whole-stage review；不执行 Stage 9。

本轮只复审 Stage 8 Phase 8.1、8.2、8.3 的 evidence、人工确认、停止条件和状态文件。
不执行 GitHub main upload，不执行 Stage 9，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只做 Stage 8 整阶段复审：

1. 复审 Phase 8.1 自动验收：route click、entry version、data state、report center。
2. 复审 Phase 8.2 截图验收：app、localhost、10 个一级入口、移动端响应式、app/localhost bundle hash。
3. 复审 Phase 8.3 人工验收：用户回复 `1` 作为通过确认来源，manual checklist 和 defects/open items 已记录。
4. 生成 `STAGE8_WHOLE_STAGE_REVIEW.md` 和 `whole_stage_review/evidence.json`，记录 findings、修复、命令、风险、回滚和下一 gate。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
PFI/tests/test_v024_stage8_whole_review_contract.py
PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md
PFI/docs/pfi_v024/STAGE8_WHOLE_STAGE_REVIEW.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_8/whole_stage_review/*
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
PFI/HANDOFF.md
PFI/docs/pfi_v024/*
PFI/reports/pfi_v024/stage_8/phase_8_1/*
PFI/reports/pfi_v024/stage_8/phase_8_2/*
PFI/reports/pfi_v024/stage_8/phase_8_3/*
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase83_manual_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/whole_stage_review/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute GitHub main upload.
- Do not execute Stage 9 regression freeze.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.

## Stop Condition

停止在 `Stage 8 whole-stage review pass`。下一轮只能进入 `Stage 8 GitHub main upload gate`，上传完成后才允许进入 Stage 9。
