# PFI v0.2.4 Run Contract

## Current Run

本轮只执行：PFI v0.2.4 `Stage 9 / Phase 9.1 - 回归规则`。

历史前置已完成：

- `Stage 8 / Phase 8.1 - 自动验收`
- `Stage 8 / Phase 8.2 - 截图验收`。历史 Phase 8.2 当轮停止条件为：不执行 Phase 8.3。
- `Stage 8 / Phase 8.3 - 人工验收`。历史 Phase 8.3 当轮停止条件为：不执行 Stage 8 whole-stage review，不执行 Stage 9。
- `Stage 8 whole-stage review - 复审并解决暴露问题`

Stage 8 GitHub main upload 已完成并经 terminal 证明 `HEAD == origin/main == remote main`。本轮只建立 Stage 9 Phase 9.1 回归防线规则；不执行 Phase 9.2 交付冻结，不执行 Phase 9.3 用户验收，不执行 Stage 9 whole-stage review，不上传 GitHub main，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## Goal

1. 确认 Stage 8 GitHub main upload evidence 存在且远端一致性已验证。
2. 新增 Stage 9 Phase 9.1 regression guardrail 合同与测试。
3. Guardrail 覆盖旧 UI signature、入口堆叠、假零、mock 财务数据，并定义机械文案和暗色控制台默认风格防线。
4. 生成 `STAGE9_REGRESSION_FREEZE.md` 和 `stage_9/phase_9_1/` evidence pack。
5. 运行 Stage 9 Phase 9.1 测试、Stage 8 相邻边界回归、JSON、py_compile、diff 和 changed-files 对账。

## Allowed Files

```text
PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py
PFI/tests/test_v024_stage9_phase91_regression_guardrails.py
PFI/docs/pfi_v024/STAGE9_REGRESSION_FREEZE.md
PFI/docs/pfi_v024/RUN_CONTRACT.md
PFI/reports/pfi_v024/stage_9/phase_9_1/*
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
PFI/web/index.html
PFI/web/app/shell.js
PFI/web/app/data_state.js
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md
/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip
```

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage9_phase91_regression_guardrails.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_github_upload_contract.py PFI/tests/test_v024_stage8_whole_review_contract.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py
python3 -m json.tool PFI/reports/pfi_v024/stage_9/phase_9_1/evidence.json
python3 -m json.tool PFI/reports/pfi_v024/stage_9/phase_9_1/regression_guardrails.json
git diff --check -- PFI
```

## Explicit Non-Goals

- Do not execute Stage 9 Phase 9.2 delivery freeze.
- Do not execute Stage 9 Phase 9.3 user acceptance.
- Do not execute Stage 9 whole-stage review.
- Do not upload GitHub main in this phase run.
- Do not reinstall or mutate app bundles.
- Do not modify launcher C or Info.plist.
- Do not write, clean, delete, synthesize, or backfill user financial data.
- Do not add forbidden placeholder financial data.

## Stop Condition

停止在 `Stage 9 / Phase 9.1 - 回归规则 candidate pass`。Phase 9.2 下一轮再进入。
