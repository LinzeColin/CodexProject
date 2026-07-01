# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 8 / Phase 8.1 - 自动验收`。

不执行 Phase 8.2，不执行 Phase 8.3，不执行 Stage 8 whole-stage review，
不执行 Stage 9，不上传 GitHub main，不重装 app bundle，不修改 launcher C/Info.plist，
不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只做 Stage 8 的自动验收 phase：

1. `T8.1.1` 路由点击测试：真实浏览器验证 10 个一级入口、核心二级页面和 back/forward。
2. `T8.1.2` 入口版本测试：验证 v0.2.4 / v0.2.3-repair / build id / bundle hash / UI contract。
3. `T8.1.3` 数据状态测试：验证 Stage 4 真实 read model 状态、8815 条记录、4 个 raw files、阻断状态和非假零。
4. `T8.1.4` 报告中心测试：验证 Stage 7 报告中心 6 类报告、公式、参数、样本量、数据范围、缺口和复核入口。
5. 生成 Phase 8.1 自动验收 evidence pack，并停止等待下一 phase 指令。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js
PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py
PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_8/phase_8_1/*
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
PFI/reports/pfi_v024/stage_2/phase_2_3/*
PFI/reports/pfi_v024/stage_3/phase_3_3/*
PFI/reports/pfi_v024/stage_4/phase_4_2/read_model_status.json
PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json
PFI/reports/pfi_v024/stage_7/phase_7_1/report_schema.json
PFI/reports/pfi_v024/stage_7/github_main_upload/evidence.json
PFI/web/index.html
PFI/web/app/version.js
PFI/web/app/entry_audit.js
PFI/web/app/data_state.js
PFI/web/app/pages/stage5Subpages.js
PFI/web/app/pages/reports.js
PFI/web/app/shell.js
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/Documents/Codex/CodexProject/EEI/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage7_github_upload_contract.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/route_click_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/entry_version_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/data_state_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_1/report_center_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 8.2 screenshot acceptance.
- Do not execute Phase 8.3 manual acceptance.
- Do not execute Stage 8 whole-stage review.
- Do not execute Stage 8 GitHub main upload.
- Do not execute Stage 9 regression freeze.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
