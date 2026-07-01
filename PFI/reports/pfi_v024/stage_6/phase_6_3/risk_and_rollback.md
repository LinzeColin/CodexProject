# Stage 6 Phase 6.3 Risk and Rollback

## Scope

本轮只完成 `Stage 6 / Phase 6.3 - 触感与设置隔离`。修改集中在 navigator.vibrate 能力检测、设置页反馈开关模型和不支持设备的静默降级。

## Risks

- `PFI/web/app/shell.js` 新增 haptic capability dataset，可能影响对 body dataset 的自动化断言。
- `PFI/web/app/pages/settings.js` 新增 v0.2.4 设置模型；旧 v0.2.3 API 保留。
- 本轮不做整阶段浏览器截图验收；截图属于 Stage 6 whole-stage review。

## Rollback

如 Phase 6.3 需要回滚，撤销以下文件的本轮变更即可：

- `PFI/web/index.html`
- `PFI/web/app/feedback.js`
- `PFI/web/app/pages/settings.js`
- `PFI/web/app/shell.js`
- `PFI/tests/test_v024_stage6_phase63_haptics_settings.py`
- `PFI/docs/pfi_v024/STAGE6_HAPTICS_SETTINGS.md`
- `PFI/reports/pfi_v024/stage_6/phase_6_3/`
- 三基与 handoff/status 文档中的 Stage 6 Phase 6.3 记录

## Explicit Non-Goals

- 不执行 Stage 6 whole-stage review。
- 不执行 GitHub main upload。
- 不重装或改写 PFI.app。
- 不写入、清理、删除、补造或改写真实财务数据。
