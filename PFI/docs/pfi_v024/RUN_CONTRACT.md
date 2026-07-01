# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 5 / Phase 5.3 - 交互状态`。

不执行 Stage 5 whole-stage review 或 GitHub main upload。

## Goal

按 repair roadmap 的 Stage 5 第三阶段，把 Phase 5.2 的 45 个二级业务页面补齐可验收交互状态：

1. 每个二级页面都有 `loading / success / error / empty` 四态。
2. 空状态必须是中文可行动状态，不只是解释文字。
3. 错误状态必须提供重试或返回业务路径动作。
4. 后退/前进验收覆盖 route alias、`pushState`、`replaceState`、`hashchange`、`popstate` 和 route state preservation。
5. app/localhost 静态 bundle 同步加载 `ux_state.js`。

## Allowed Files

```text
PFI/web/app/ux_state.js
PFI/web/app/shell.js
PFI/web/index.html
PFI/web/styles.css
PFI/src/pfi_os/app/streamlit_app.py
PFI/tests/test_v024_stage5_phase53_interaction_states.py
PFI/docs/pfi_v024/STAGE5_INTERACTION_STATES.md
PFI/reports/pfi_v024/stage_5/phase_5_3/*
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
PFI/web/app/pages/stage5Subpages.js
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/ux_state.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/src/pfi_os/app/streamlit_app.py PFI/tests/test_v024_stage5_phase53_interaction_states.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_phase53_interaction_states.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_3/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_3/ux_state_validation.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_3/history_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not run Stage 5 whole-stage review in this phase run.
- Do not upload to GitHub main before Stage 5 whole-stage review and fixes.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
