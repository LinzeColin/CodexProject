# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 8 GitHub main upload gate`。

历史前置已完成：

- `Stage 8 / Phase 8.1 - 自动验收`
- `Stage 8 / Phase 8.2 - 截图验收`。历史 Phase 8.2 当轮停止条件为：不执行 Phase 8.3。
- `Stage 8 / Phase 8.3 - 人工验收`。历史 Phase 8.3 当轮停止条件为：不执行 Stage 8 whole-stage review，不执行 Stage 9。
- `Stage 8 whole-stage review - 复审并解决暴露问题`

本轮只负责把已复审的 Stage 8 package 上传到 GitHub main，并用 terminal 证明 `HEAD == origin/main == remote main`。不执行 Stage 9，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

1. 确认 Stage 8 whole-stage review pass。
2. 确认当前 branch 已 rebase 到最新 `origin/main`，上传前 ahead/behind 为 `4/0`。
3. 生成 `STAGE8_GITHUB_MAIN_UPLOAD.md` 和 `stage_8/github_main_upload/evidence.json`。
4. 运行 Stage 8 upload gate regression、whole-review regression、phase regressions、JSON、py_compile、diff 和 changed-files 对账。
5. `git push origin HEAD:main`。
6. fresh fetch 后验证 `HEAD == origin/main == remote main`。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
PFI/tests/test_v024_stage8_github_upload_contract.py
PFI/docs/pfi_v024/STAGE8_GITHUB_MAIN_UPLOAD.md
PFI/docs/pfi_v024/STAGE8_E2E_ACCEPTANCE.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_8/github_main_upload/*
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
PFI/reports/pfi_v024/stage_8/whole_stage_review/*
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_github_upload_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase83_manual_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/github_main_upload/evidence.json
git diff --check -- PFI
git push origin HEAD:main
git fetch origin main
git ls-remote origin refs/heads/main
```

## Explicit Non-Goals

- Do not execute Stage 9 regression freeze.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.

## Stop Condition

停止在 `Stage 8 GitHub main upload complete`，且 terminal 证明 `HEAD == origin/main == remote main`。Stage 9 下一轮再进入。
