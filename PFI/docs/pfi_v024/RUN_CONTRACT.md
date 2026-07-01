# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 8 / Phase 8.2 - 截图验收`。

不执行 Phase 8.3，不执行 Stage 8 whole-stage review，不执行 Stage 9，
不上传 GitHub main，不重装 app bundle，不修改 launcher C/Info.plist，
不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只做 Stage 8 的截图验收 phase：

1. `T8.2.1` app 截图：通过当前 checkout 启动临时 Streamlit 服务，使用存在且指向当前 checkout 的 `PFI.app` 入口参数采集 `app_home.png`。
2. `T8.2.2` localhost 截图：通过同一临时服务采集 `localhost_home.png`，并验证 app/localhost bundle hash 一致。
3. `T8.2.3` 10 入口截图：真实浏览器逐项点击 10 个正式一级入口并生成截图索引。
4. `T8.2.4` 移动端响应式截图：采集 `mobile_responsive.png`，验证移动端水平溢出为 `0px`。
5. 生成 Phase 8.2 screenshot evidence pack，并停止等待下一 phase 指令。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
PFI/scripts/validate_v024_stage8_phase82_screenshots.js
PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py
PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_8/phase_8_2/*
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
PFI/reports/pfi_v024/stage_2/phase_2_3/*
PFI/web/index.html
PFI/web/app/*.js
PFI/web/app/pages/*.js
PFI/src/pfi_os/app/streamlit_app.py
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/Documents/Codex/CodexProject/EEI/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage8_phase82_screenshots.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/scripts/validate_v024_stage8_phase82_screenshots.js
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/browser_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/screenshot_index.json
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_2/app_entry_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 8.3 manual acceptance.
- Do not execute Stage 8 whole-stage review.
- Do not execute Stage 8 GitHub main upload.
- Do not execute Stage 9 regression freeze.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.
