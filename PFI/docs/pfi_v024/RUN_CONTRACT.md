# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `v0.2.4 overall project review`。

历史前置已完成：

- `Stage 8 / Phase 8.1 - 自动验收`
- `Stage 8 / Phase 8.2 - 截图验收`。历史 Phase 8.2 当轮停止条件为：不执行 Phase 8.3。
- `Stage 8 / Phase 8.3 - 人工验收`。历史 Phase 8.3 当轮停止条件为：不执行 Stage 8 whole-stage review，不执行 Stage 9。
- `Stage 8 whole-stage review - 复审并解决暴露问题`
- `Stage 7 / Phase 7.3 - 验收`
- `Stage 7 whole-stage review`

Stage 8 GitHub main upload 已完成并经 terminal 证明 `HEAD == origin/main == remote main`。Stage 8.3 用户验收已由用户回复 `1` 确认。Stage 9 Phase 9.1 回归防线已 candidate pass，Stage 9 Phase 9.2 交付冻结候选包已 candidate pass，Stage 9.3 用户验收已由用户回复 `1` 确认。`Stage 9 whole-stage review - 复审并解决暴露问题` 已 pass，Stage 9 GitHub main upload 已完成。本轮只执行 v0.2.4 overall project review；future version 未开始，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

1. 确认 Stage 0-9 evidence chain 存在并可回归。
2. 明确 Stage 8.3 和 Stage 9.3 用户验收已由用户回复 `1` 确认，不作为阻塞项。
3. 新增 v0.2.4 overall project review 合同与测试。
4. 生成 `OVERALL_PROJECT_REVIEW.md`、`overall_project_review/evidence.json` 和 `review_audit.json`。
5. 运行 overall review 测试、Stage 0-9 回归、JSON、py_compile、Node shell check、diff 和 changed-files 对账。
6. 提交后 push `HEAD:main`，再用 terminal 验证 `HEAD == origin/main == remote main`。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py
PFI/src/pfi_v02/stage_v024_overall_project_review.py
PFI/tests/test_v024_overall_project_review.py
PFI/tests/test_v024_stage9_github_upload_contract.py
PFI/tests/test_v024_stage9_whole_review_contract.py
PFI/tests/test_v024_stage9_phase93_user_acceptance.py
PFI/tests/test_v024_stage9_phase92_delivery_freeze.py
PFI/tests/test_v024_stage9_phase91_regression_guardrails.py
PFI/docs/pfi_v024/STAGE9_REGRESSION_FREEZE.md
PFI/docs/pfi_v024/STAGE9_WHOLE_STAGE_REVIEW.md
PFI/docs/pfi_v024/STAGE9_GITHUB_MAIN_UPLOAD.md
PFI/docs/pfi_v024/OVERALL_PROJECT_REVIEW.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_9/whole_stage_review/*
PFI/reports/pfi_v024/stage_9/github_main_upload/*
PFI/reports/pfi_v024/overall_project_review/*
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
PFI/reports/pfi_v024/stage_8/github_main_upload/*
PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/*
PFI/reports/pfi_v024/stage_9/phase_9_1/*
PFI/reports/pfi_v024/stage_9/phase_9_2/*
PFI/reports/pfi_v024/stage_9/phase_9_3/*
PFI/web/index.html
PFI/web/app/shell.js
PFI/web/app/data_state.js
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_overall_project_review.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_github_upload_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_phase93_user_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_phase92_delivery_freeze.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_phase91_regression_guardrails.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_github_upload_contract.py -q
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_overall_project_review.py
python3 -m json.tool PFI/reports/pfi_v024/overall_project_review/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/overall_project_review/review_audit.json
python3 -m json.tool PFI/reports/pfi_v024/stage_9/github_main_upload/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_9/whole_stage_review/evidence.json
git diff --check -- PFI
git push origin HEAD:main
git ls-remote origin refs/heads/main
```

## Explicit Non-Goals

- Do not start future version work.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.

## Stop Condition

停止在 `v0.2.4 overall project review` 且 terminal 证明 `HEAD == origin/main == remote main`。future version 未开始，后续版本必须下一轮在用户明确指令后再进入。
