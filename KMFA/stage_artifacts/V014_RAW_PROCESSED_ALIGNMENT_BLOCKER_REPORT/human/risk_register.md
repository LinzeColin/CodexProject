# Risk Register

| risk_id | risk | mitigation | status |
| --- | --- | --- | --- |
| RPA-BLOCK-001 | 把证据不足误判为业务值不一致 | 明确 comparable value pairs 为 0，当前不能做业务值差异结论 | controlled |
| RPA-BLOCK-002 | public report 泄露 raw/private 明细 | 只输出聚合计数、状态和允许输入结构 | controlled |
| RPA-BLOCK-003 | 外部 agent 建议越权执行 | 报告内锁定禁止 upload、reinstall、formal report 和业务动作 | controlled |
