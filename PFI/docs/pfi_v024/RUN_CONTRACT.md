# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 6 whole-stage review - 复审并解决暴露问题`。

不执行 Stage 7，不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Goal

根据 `PFI_v0.2.3_Repair_Roadmap.md` 和 TaskPack，本轮只复审 Stage 6 Phase 6.1、6.2、6.3：

1. 复审默认浅色设计系统、token、状态色、卡片/表格/图表槽和响应式布局。
2. 复审页面切换、加载、保存、失败、阻断、报告生成的适度动效。
3. 复审触感能力检测、可关闭设置、不支持静默降级和设置页隔离。
4. 生成 review-time 亮色桌面、移动响应式和设置隔离浏览器证据。
5. 修复复审暴露问题并记录 evidence。

## Allowed Files

```text
PFI/web/styles.css
PFI/web/app/shell.js
PFI/scripts/validate_v024_stage6_whole_review_browser.js
PFI/tests/test_v024_stage6_whole_review_contract.py
PFI/docs/pfi_v024/STAGE6_WHOLE_STAGE_REVIEW.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_6/whole_stage_review/*
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
PFI/reports/pfi_v024/stage_6/phase_6_1/*
PFI/reports/pfi_v024/stage_6/phase_6_2/*
PFI/reports/pfi_v024/stage_6/phase_6_3/*
PFI/reports/pfi_v024/stage_5/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PLAYWRIGHT_PACKAGE_PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.1/node_modules/playwright" PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node PFI/scripts/validate_v024_stage6_whole_review_browser.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage6_phase61_design_system.py PFI/tests/test_v024_stage6_phase62_motion_feedback.py PFI/tests/test_v024_stage6_phase63_haptics_settings.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_phase51_home_rebuild.py PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py PFI/tests/test_v024_stage5_phase53_interaction_states.py -q
PATH="/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" node --check PFI/web/app/shell.js
python3 -m json.tool PFI/reports/pfi_v024/stage_6/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_6/whole_stage_review/browser_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 7.
- Do not upload to GitHub main.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
