# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 8 / Phase 8.3 - 人工验收`。

前置已完成：`Stage 8 / Phase 8.2 - 截图验收`。历史 Phase 8.2 当轮停止条件为：不执行 Phase 8.3。

本轮产出人工验收清单、缺陷/开放项定位和 pending-user-confirmation evidence。
不执行 Stage 8 whole-stage review，不执行 Stage 9，不上传 GitHub main，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只做 Stage 8 的人工验收准备 phase：

1. `T8.3.1` 人工验收清单：生成 `manual_acceptance.md`，列出打开 PFI.app、打开 localhost、10 个一级入口、核心二级页面、浏览器后退/前进、核心指标无假零、报告中心、亮色 UI 和移动端响应式检查项。
2. `T8.3.2` 失败项定位：生成 `defects.md`，记录待用户人工验收和 `/Applications/PFI.app` 缺失、`~/Downloads/PFI.app` 可用的环境项。
3. `T8.3.3` 不进入下一 Stage 规则：生成 machine-readable evidence，明确用户确认前不进入 Stage 8 whole-stage review、Stage 9 或 GitHub main upload。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
PFI/tests/test_v024_stage8_phase83_manual_acceptance.py
PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_8/phase_8_3/*
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
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase83_manual_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not claim user acceptance before explicit user confirmation.
- Do not execute Stage 8 whole-stage review.
- Do not execute Stage 8 GitHub main upload.
- Do not execute Stage 9 regression freeze.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.

## Stop Condition

停止在 `ready_for_user_acceptance`。下一轮只有在用户明确确认或明确指令后，才能进入 Stage 8 whole-stage review 或修复轮。
