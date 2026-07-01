# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 5 whole-stage review - 复审并解决暴露问题`。

不执行 GitHub main upload，不进入 Stage 6。

## Goal

复审 Stage 5 三个 phase 是否共同满足 repair roadmap 的人类任务流验收：

1. Phase 5.1 首页只回答钱、位置、变化、问题、下一步、依据。
2. Phase 5.2 10 个正式一级入口均有 3 个以上差异化二级页面。
3. Phase 5.3 每个页面有主操作、loading/success/error/empty 状态和可回退 route。
4. 复审截图覆盖每个一级入口和核心二级页面。
5. 复审暴露问题必须修复后才能进入 GitHub main upload gate。

## Allowed Files

```text
PFI/scripts/validate_v024_stage5_whole_review_browser.js
PFI/web/app/shell.js
PFI/web/index.html
PFI/src/pfi_os/app/streamlit_app.py
PFI/tests/test_v024_stage5_whole_review_contract.py
PFI/docs/pfi_v024/STAGE5_WHOLE_STAGE_REVIEW.md
PFI/reports/pfi_v024/stage_5/whole_stage_review/*
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
PFI/web/app/routes.js
PFI/web/app/pages/home.js
PFI/web/app/pages/stage5Subpages.js
PFI/web/app/ux_state.js
PFI/reports/pfi_v024/stage_5/phase_5_1/*
PFI/reports/pfi_v024/stage_5/phase_5_2/*
PFI/reports/pfi_v024/stage_5/phase_5_3/*
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/scripts/validate_v024_stage5_whole_review_browser.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_os/app/streamlit_app.py PFI/tests/test_v024_stage5_whole_review_contract.py
PLAYWRIGHT_PACKAGE_PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node PFI/scripts/validate_v024_stage5_whole_review_browser.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_whole_review_contract.py PFI/tests/test_v024_stage5_phase51_home_rebuild.py PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py PFI/tests/test_v024_stage5_phase53_interaction_states.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage3_phase32_route_implementation.py PFI/tests/test_v024_stage4_phase42_read_model_link.py PFI/tests/test_v024_stage4_phase43_acceptance.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_5/whole_stage_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/whole_stage_review/browser_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not upload to GitHub main in this review run.
- Do not enter Stage 6.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
