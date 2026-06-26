# RiskAndLimits

## Research Only

PFIOS 仅用于研究、回测和辅助分析。

PFIOS is for research, backtesting, and assisted analysis only.

PFIOS 产出的结果可以作为实盘交易前的参考，但不能保证收益。

PFIOS outputs may support real trading decisions, but they do not guarantee profit.

## Known Risks

数据错误会导致策略结果错误。

Data errors can produce incorrect strategy results.

回测成本假设过低会夸大策略收益。

Underestimated transaction costs can overstate strategy returns.

参数过拟合会导致历史表现好但未来失效。

Parameter overfitting can make historical results look strong while future performance fails.

分钟级数据缺口会影响短周期策略。

Missing minute-level data can affect short-interval strategies.

## No Live Trading

系统禁止实盘交易。

Live trading is prohibited.

系统禁止真实下单。

Real order submission is prohibited.

系统禁止调用交易 API。

Trade API calls are prohibited.

未确认策略会被回测引擎拒绝运行。

Unapproved strategies are blocked by the backtest engine.
