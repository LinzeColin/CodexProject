# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 5 / Phase 5.1 - 首页重建`。

不执行 Phase 5.2、Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload。

## Goal

按 repair roadmap 的 Stage 5 第一阶段，把首页从机械功能入口恢复为人类任务流首页：

1. 首页只保留六个核心问题：钱、位置、变化、问题、下一步、依据。
2. 移除默认 `功能面板 / PFI 功能入口 / 功能已准备 / 进入操作面板` 机械层。
3. 首页生成下一步任务流，但不进入 Phase 5.2 的二级页面差异化。
4. 首页接入 Stage 4 的真实 `read_model_status` 数据状态卡。
5. 缺失/未挂链指标继续显示中文状态，不显示 `CNY 0.00`。

## Allowed Files

```text
PFI/web/index.html
PFI/web/app/pages/home.js
PFI/web/app/shell.js
PFI/web/styles.css
PFI/tests/test_v024_stage5_phase51_home_rebuild.py
PFI/docs/pfi_v024/STAGE5_HOME_REBUILD.md
PFI/reports/pfi_v024/stage_5/phase_5_1/*
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
PFI/reports/pfi_v024/stage_4/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/pages/home.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/tests/test_v024_stage5_phase51_home_rebuild.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_phase51_home_rebuild.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_1/evidence.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 5.2 二级页面差异化.
- Do not execute Phase 5.3 交互状态.
- Do not run Stage 5 whole-stage review in this phase run.
- Do not upload to GitHub main before Stage 5 whole-stage review and fixes.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
