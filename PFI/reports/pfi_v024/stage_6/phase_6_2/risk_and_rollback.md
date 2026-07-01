# Stage 6 Phase 6.2 Risk and Rollback

## Scope

本轮只完成 `Stage 6 / Phase 6.2 - 动效反馈`。修改集中在页面切换、加载骨架、成功/失败/阻断反馈和报告生成进度的轻量动效。

## Risks

- `PFI/web/app/shell.js` 新增 route transition 和 feedback state 数据标记，可能影响自动化测试中对 dataset 的断言。
- `PFI/web/styles.css` 新增 v0.2.4 motion block，可能改变同一页面上已有反馈区域的视觉节奏。
- 本轮未做真实浏览器截图验收；截图属于 Stage 6 pass gate 或整阶段复审后续工作。

## Rollback

如 Phase 6.2 需要回滚，撤销以下文件的本轮变更即可：

- `PFI/web/index.html`
- `PFI/web/styles.css`
- `PFI/web/app/shell.js`
- `PFI/web/app/feedback.js`
- `PFI/tests/test_v024_stage6_phase62_motion_feedback.py`
- `PFI/docs/pfi_v024/STAGE6_MOTION_FEEDBACK.md`
- `PFI/reports/pfi_v024/stage_6/phase_6_2/`
- 三基与 handoff/status 文档中的 Stage 6 Phase 6.2 记录

## Explicit Non-Goals

- 不执行 Phase 6.3 触感与设置隔离。
- 不执行 Stage 6 whole-stage review。
- 不执行 GitHub main upload。
- 不重装或改写 PFI.app。
- 不写入、清理、删除、补造或改写真实财务数据。
