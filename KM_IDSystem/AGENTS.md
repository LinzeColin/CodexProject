# KM_IDSystem Agent 规则

默认用户可见输出使用中文。

## S4 精简执行胶囊

普通任务先读本文件、`README.md` 和被任务直接点名的任务/证据文件；不得扫描无关项目。

- 不得读取完整 `模型参数文件.md`，除非变更涉及路由、优化规则、安全策略、评分、阈值、
  模型参数或发布验收。
- 治理验证：`python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`。
- owner 预览：`python -B scripts/lean_governance.py check-render --project KM_IDSystem`。
- 应用变更先补任务点名的窄后端/前端测试，再考虑 broad test discovery。

## 边界

- 不得编造 owner 决策或生产就绪结论。
- 数据、缓存、本地运行输出和 secrets 不得进入 Git，除非当前任务明确允许提交脱敏证据。
