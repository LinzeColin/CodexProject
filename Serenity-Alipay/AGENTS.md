# Serenity-Alipay Agent 规则

默认用户可见输出使用中文。

## S4 精简执行胶囊

普通任务先读本文件、`README.md` 和被任务直接点名的任务/证据文件；普通 UI/docs 变更不得读取
完整项目历史。

- 不得读取完整 `模型参数文件.md`，除非变更涉及基金评分、费用、分配公式、人工复核门禁、
  通知严重级别、交易/平台检查或生产验收。
- 治理验证：`python -B scripts/lean_governance.py validate --project Serenity-Alipay --semantic`。
- owner 预览：`python -B scripts/lean_governance.py check-render --project Serenity-Alipay`。
- 应用变更要补 `Serenity-Alipay/tests/` 下覆盖被修改模块的聚焦测试。

## 边界

- 不得提交支付宝动作、券商订单、支付、转账或实盘交易指令。
- 个人财务数据、凭据、本地运行数据库和输出 artifacts 不得进入 Git，除非当前任务明确允许提交脱敏证据。
