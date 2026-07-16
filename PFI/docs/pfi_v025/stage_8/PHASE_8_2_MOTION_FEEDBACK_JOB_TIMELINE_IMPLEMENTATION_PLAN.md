# PFI v0.2.5 Stage 8 Phase 8.2 实施记录

## 唯一验收目标

- Phase：`V025-S8-P8.2 动效、反馈、触感与长任务`
- Tasks：`S8-P2-T1`、`S8-P2-T2`、`S8-P2-T3`、`S8-P2-T4`
- Acceptance：`ACC-PFI-V025-STAGE8-WHOLE-REVIEW`
- 本轮只形成 Phase 8.2 candidate pass；Phase 8.3 与 Stage 8 whole-stage review 均未开始。

## 实施范围

1. `web/app/motion.js` 固定 100/300/1000/10000ms 反馈预算、220ms 动效上限、`prefers-reduced-motion` 零时长降级，以及 View Transition 渐进增强。
2. `web/app/haptics.js` 将触感和声音设为显式 opt-in，检测 `navigator.vibrate`、Web Audio 与 user activation；不支持或未授权时只保留视觉反馈且不报错。
3. `web/app/components/jobTimeline.js` 提供 queued/running/blocked/succeeded/failed/cancelled 状态、session 级跨路由保留和 10 秒 durable 标识。
4. 进度条只在同时存在 `completedUnits` 与 `totalUnits` 时显示；时间经过只改变“等待/后台运行”状态，永不换算成百分比。
5. 缓存刷新反馈改为等待真实本机 API Promise：300ms 后才显示 skeleton，1 秒后显示真实阶段，10 秒后显示 durable，settle 后取消全部未触发计时器。
6. official Streamlit candidate 按 canonical `index.html` script refs 动态内联全部前端来源，避免新组件只在静态壳层可用。

## 真实验证

- RED：实现前 7/7 Phase 8.2 合同测试失败，覆盖缺失运行时、旧默认、假百分比、缺失时间线与证据。
- GREEN：专项合同 7/7；旧 Stage 6 反馈、Phase 8.1 设计系统兼容 16/16。
- official candidate/release/Stage 7 兼容集 56/56，通过 19 个 canonical frontend sources 精确内联校验。
- Playwright + local Chrome：16/16 门禁；常规动效、显式触觉、真实 2/4 工作量、11 秒 durable、跨路由保留、300ms skeleton、reduced-motion 与无能力降级均通过。
- 浏览器控制台、page error、HTTP error、外部请求均为 0；trace 仅保留 3 个 action timeline 条目，绝对路径、token、请求体与私有值扫描为 0。

## Release identity

新增 canonical frontend scripts 并修改 shell/styles/index，因此更新 frontend bundle hash。official candidate 资产注入器属于 backend identity source，因此同步更新 backend build hash。版本、build id、data schema、公式版本和参数版本均不改变。

## 非目标与停止边界

- 未开始 Phase 8.3 WCAG 自动化、键盘全流程、视觉回归和人工质感验收。
- 未开始 Stage 8 whole-stage review 或 Stage 8 user acceptance。
- 未读取或修改财务数据、数据库、模型、公式或参数。
- 未 push、未安装 PFI.app、未执行 production/final acceptance。
- 未使用 Finder、LaunchServices 或任何 GUI 文件操作。

回滚以本 Phase 单一提交为边界；前后端 release hash 必须与对应源码一起回滚。
