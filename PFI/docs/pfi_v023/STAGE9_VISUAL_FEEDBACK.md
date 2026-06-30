# PFI v0.2.3 Stage 9 Visual Feedback

## Stage 9 Phase 9.1 设计系统

Phase 9.1 只建立明亮视觉设计系统，不实现动效反馈，不实现触感反馈，不新增设置页反馈偏好。

本 phase 覆盖：

- `T9.1.1` 亮色 token：在后置正式入口 `PFI/web/styles.css` 中增加 v0.2.3 light token，并覆盖旧暗色偏好。
- `T9.1.2` 卡片/表格/按钮规范：统一卡片、表格、主按钮、次按钮、二级入口和移动入口的圆角、边框、层级和最小点击高度。
- `T9.1.3` 图表空状态规范：为趋势空态和 `v023-chart-empty` 提供中文真实空态，不展示财务假 0。
- `T9.1.4` 移动端适配：移动端使用单列工作区、底部一级入口横向滚动、按钮文本可换行，避免文字挤压。

实现边界：

- 当前页面已按顺序加载 `PFI/web/styles/tokens.css` 和 `PFI/web/styles.css`；Phase 9.1 使用后置 `styles.css` 作为当前 v0.2.3 设计系统覆盖层。
- 不修改 route、数据计算、报告生成、反馈 JS 或设置页逻辑。
- 不使用禁用英文占位财务数据词参与验收。

Phase 9.1 证据：

- `PFI/reports/pfi_v023/stage_9/phase_9_1/evidence.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_1/design_system_audit.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_1/no_source_term_scan.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_1/terminal.log`

## Stage 9 Phase 9.2 动效反馈

Phase 9.2 只实现状态服务型动效反馈，不实现触感反馈，不新增设置页反馈偏好，不执行 Stage 9 whole-stage review。

本 phase 覆盖：

- `T9.2.1` 页面转场：定义 `data-route-transition` 进入/退出状态和 180ms 页面切换动效，上限不超过 220ms。
- `T9.2.2` `loading/success/error/blocked` 状态组件：为全局 action feedback 和骨架屏提供差异化视觉状态。
- `T9.2.3` 报告生成进度：定义报告范围、真实数据状态检查、公式与参数、可复核报告 4 步进度模型。
- `T9.2.4` 减少动画模式：支持 `prefers-reduced-motion` 和 `body.reduce-motion`，将 transition/animation 降为 1ms 并关闭页面进入动画。

实现边界：

- `PFI/web/app/feedback.js` 只提供可测试的 Phase 9.2 feedback model，不绑定触感，不修改 app 启动入口。
- `PFI/web/styles.css` 提供当前页面可用的转场、状态和报告进度样式。
- 不修改 route、数据计算、报告生成、触感能力检测或设置页开关。

Phase 9.2 证据：

- `PFI/reports/pfi_v023/stage_9/phase_9_2/evidence.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_2/feedback_audit.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_2/no_source_term_scan.json`
- `PFI/reports/pfi_v023/stage_9/phase_9_2/terminal.log`

Phase 9.3 未执行。

Stage 9 whole-stage review 未执行。

GitHub main upload 未执行。
