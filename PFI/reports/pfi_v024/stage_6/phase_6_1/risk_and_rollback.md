# Stage 6 Phase 6.1 Risk and Rollback

## Scope

本轮只完成 `Stage 6 / Phase 6.1 - 设计系统`。修改集中在浅色 token、状态色、卡片/表格/图表槽样式、响应式布局和对应机器证据。

## Risks

- `PFI/web/styles.css` 追加目标版本覆盖层，可能影响同一页面上继承 `data-pfi-target-version="v0.2.4"` 的既有 Stage 5 组件视觉。
- `PFI/web/index.html` 将 color scheme 锁为 `light`，会让系统暗色偏好不再自动切换为暗色。
- 本轮没有进行真实浏览器截图验收；截图属于 Stage 6 pass gate 或整阶段复审的后续工作。

## Rollback

如 Phase 6.1 需要回滚，撤销以下文件的本轮变更即可：

- `PFI/web/index.html`
- `PFI/web/styles.css`
- `PFI/tests/test_v024_stage6_phase61_design_system.py`
- `PFI/docs/pfi_v024/STAGE6_DESIGN_SYSTEM.md`
- `PFI/reports/pfi_v024/stage_6/phase_6_1/`
- 三基与 handoff/status 文档中的 Stage 6 Phase 6.1 记录

## Explicit Non-Goals

- 不执行 Phase 6.2 动效反馈。
- 不执行 Phase 6.3 触感与设置隔离。
- 不执行 Stage 6 whole-stage review。
- 不执行 GitHub main upload。
- 不重装或改写 PFI.app。
- 不写入、清理、删除、补造或改写真实财务数据。
