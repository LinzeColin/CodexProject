# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 5 / Phase 5.2 - 二级页面差异化`。

不执行 Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload。

## Goal

按 repair roadmap 的 Stage 5 第二阶段，把 10 个正式一级入口的二级页面固定为真实业务页面目录：

1. 每个一级入口至少 3 个差异化二级页面。
2. 二级页面的 URL、state、title、layout、primary action、data object 不同。
3. 页面目录与 Stage 3 secondary routes 对齐。
4. shell runtime 优先读取 `PFI_V024_STAGE5_PAGES`。
5. app/localhost 静态 bundle 同步加载 `stage5Subpages.js`。

## Allowed Files

```text
PFI/web/index.html
PFI/web/app/pages/stage5Subpages.js
PFI/web/app/shell.js
PFI/src/pfi_os/app/streamlit_app.py
PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py
PFI/docs/pfi_v024/STAGE5_SUBPAGE_DIFFERENTIATION.md
PFI/reports/pfi_v024/stage_5/phase_5_2/*
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
PFI/web/app/pages/stage4Subpages.js
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/pages/stage5Subpages.js
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py -q
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_2/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Phase 5.3 交互状态.
- Do not run Stage 5 whole-stage review in this phase run.
- Do not upload to GitHub main before Stage 5 whole-stage review and fixes.
- Do not reinstall or mutate app bundles.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add mock/sample/demo/synthetic/fixture/fake financial data.
