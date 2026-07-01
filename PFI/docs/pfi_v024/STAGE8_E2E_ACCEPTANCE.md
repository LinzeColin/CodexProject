# PFI v0.2.4 Stage 8 E2E Acceptance

## Current Run Boundary

本轮只执行 `Stage 8 Phase 8.3 - 人工验收`，当前状态为待用户确认。

不执行 Stage 8 whole-stage review、不执行 Stage 9 regression freeze，不上传 GitHub main，不重装 app bundle，不写入、清理、删除、补造或改写真实财务数据。

## Stage 8 Phase 8.1 - 自动验收

Phase 8.1 覆盖 roadmap 中的四个自动验收任务，当前状态为 candidate pass：

- `T8.1.1` 路由点击测试：10 个一级入口全部点击，核心二级页面全部直达，浏览器 back/forward 正常。
- `T8.1.2` 入口版本测试：页面运行时读取 `PFI_READ_STAGE2_ENTRY_AUDIT()`，确认 v0.2.4 / v0.2.3-repair / build id / UI contract / bundle hash。
- `T8.1.3` 数据状态测试：注入 Stage 4 真实 `read_model_status.json`，确认 `MetaDatabase/PFI` 8815 条记录、4 个 raw files、日期范围和非假零阻断状态。
- `T8.1.4` 报告中心测试：注入 Stage 7 `report_schema.json`，确认 6 类报告、公式、参数、样本量、数据范围、置信度、缺口和复核入口可由浏览器模型验证。

Phase 8.1 evidence:

- `PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_1/browser_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_1/route_click_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_1/entry_version_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_1/data_state_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_1/report_center_validation.json`

## Stage 8 Phase 8.2 - 截图验收

Phase 8.2 覆盖 roadmap 中的四个截图验收任务，当前状态为 candidate pass：

- `T8.2.1` app 截图：`app_home.png`。
- `T8.2.2` localhost 截图：`localhost_home.png`，与 app 入口 bundle hash 一致。
- `T8.2.3` 10 入口截图：10 个正式一级入口逐项截图，并生成 `desktop_all_pages.png` 截图索引。
- `T8.2.4` 移动端响应式截图：`mobile_responsive.png`，移动端水平溢出为 `0px`。

Phase 8.2 evidence:

- `PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/browser_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshot_index.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/app_entry_validation.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/app_home.png`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/localhost_home.png`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/mobile_responsive.png`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/screenshots/desktop_all_pages.png`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/terminal.log`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/changed_files.txt`
- `PFI/reports/pfi_v024/stage_8/phase_8_2/risk_and_rollback.md`

## Stage 8 Phase 8.3 - 人工验收

Phase 8.3 覆盖 roadmap 中的三个人工验收准备任务，当前状态为待用户确认：

- `T8.3.1` 人工验收清单：`manual_acceptance.md` 列出打开 PFI.app、打开 localhost、10 个一级入口、核心二级页面、浏览器后退/前进、核心指标无假零、报告中心、亮色 UI 和移动端响应式检查项。
- `T8.3.2` 失败项定位：`defects.md` 记录待用户人工验收和 `/Applications/PFI.app` 缺失、`~/Downloads/PFI.app` 可用的环境开放项。
- `T8.3.3` 不进入下一 Stage 规则：`evidence.json` 明确用户确认前不进入 Stage 8 whole-stage review、Stage 9 或 GitHub main upload。

Phase 8.3 evidence:

- `PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json`
- `PFI/reports/pfi_v024/stage_8/phase_8_3/manual_acceptance.md`
- `PFI/reports/pfi_v024/stage_8/phase_8_3/defects.md`
- `PFI/reports/pfi_v024/stage_8/phase_8_3/terminal.log`
- `PFI/reports/pfi_v024/stage_8/phase_8_3/changed_files.txt`
- `PFI/reports/pfi_v024/stage_8/phase_8_3/risk_and_rollback.md`

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase83_manual_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m py_compile PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py
python3 -m json.tool PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json
git diff --check -- PFI
```

## Explicitly Not Done

- User acceptance confirmation.
- Stage 8 whole-stage review.
- Stage 8 GitHub main upload.
- Stage 9 regression freeze.
- App bundle reinstall.
- Financial data mutation or synthesis.

## Next Gate

下一轮必须先等待用户确认人工验收结果，或按用户明确指令进入 Stage 8 whole-stage review / 修复轮。不得自动进入 Stage 9 或 upload gate。
