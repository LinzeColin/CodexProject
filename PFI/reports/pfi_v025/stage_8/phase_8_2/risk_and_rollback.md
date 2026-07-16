# Phase 8.2 风险与回滚

- 风险：状态动效阻塞输入或造成眩晕。控制：仅 transform/opacity，单次不超过 220ms；reduced-motion 实测 0ms 且状态文本保留。
- 风险：等待时间被错误显示为完成百分比。控制：只有 `completedUnits/totalUnits` 同时存在才渲染 progress value；10 秒只升级 durable 标签。
- 风险：触觉或声音未经用户同意触发。控制：双默认关闭、真实 user activation、能力检测；不支持时静默降级为 visual_only。
- 风险：离开页面后丢失长任务。控制：时间线位于跨路由 task center，并用 sessionStorage 保留有限、脱敏的任务元数据。
- 风险：计时器在真实操作 settle 后继续写入旧状态。控制：settle 时清除 skeleton/stage/durable 三个 timer，并以 terminal job state 停止后续调度。
- 风险：canonical index 新脚本未进入 official candidate。控制：candidate 注入器动态读取 canonical script refs；测试精确比对 19 个 source。
- 风险：trace 泄露本地路径或 runtime token。控制：删除 resource body，脱敏后扫描 3 个保留条目，禁用项命中均为 0。

回滚：revert 本 Phase 单一提交；前端与后端 release hash 一并回滚。本轮未改财务数据、数据库、模型、公式或参数，不需要数据回滚。
