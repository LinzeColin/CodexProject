# Guideline

## Working Principles

先理解上下文，再行动。

Understand context before action.

复杂任务先计划，不要直接修改。

Plan complex tasks before editing.

不要假设业务规则，缺失信息必须标记。

Do not assume business rules; mark missing information clearly.

涉及金额、成本、回款、工资和税费时，必须写明公式和假设。

When money, cost, collection, salary, or tax is involved, formulas and assumptions must be stated.

## Change Report

每次修改后必须说明改了什么。

After every change, state what changed.

每次修改后必须说明为什么改。

After every change, state why it changed.

每次修改后必须说明涉及哪些文件。

After every change, list affected files.

每次修改后必须说明如何验证。

After every change, explain how it was verified.

每次修改后必须说明风险和回滚建议。

After every change, explain risks and rollback advice.

## Safety Rules

系统禁止接入实盘交易。

The system must not connect to live trading.

系统禁止提交真实订单。

The system must not submit real orders.

策略修改必须经过确认或明确确认。

Strategy changes must go through approval or explicit confirmation.

未确认策略不得运行回测。

Unapproved strategies must not run backtests.

API Key 只能保存在 `.env` 或本地安全配置中。

API keys may only be stored in `.env` or local secure configuration.
