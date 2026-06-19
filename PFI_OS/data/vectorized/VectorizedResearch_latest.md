# Vectorized Research 2026-06-16

## Summary
- Status: `Pass`
- Replay Status: `Pass`
- Rows: `7`
- Symbols: `SPY`
- Selected Symbol: `SPY`
- Window: `2026-01-01T00:00:00` -> `2026-01-09T00:00:00`
- Strategy: `ma_crossover`
- Parameter Runs: `4`
- Scan Runs: `4`

## Best Run
```json
{
  "run_id": "vectorized_replay_scan_0001",
  "strategy_id": "ma_crossover",
  "created_at": "2026-06-15T18:45:54.813959+00:00",
  "param_short_window": 2,
  "param_long_window": 4,
  "total_return": -0.0021074790678844435,
  "annualized_return": -0.07313680764469654,
  "volatility": 0.012075967289886032,
  "sharpe": -6.283164192189335,
  "sortino": -3.593047067539704,
  "calmar": -34.703456256917256,
  "max_drawdown": -0.0021074790678844435,
  "win_rate": 0.5,
  "trade_count": 3,
  "buy_count": 1,
  "sell_count": 2,
  "round_trip_count": 2,
  "turnover": 1.001001,
  "average_gain": 0.13650618914885748,
  "average_loss": -0.0004972676193000707,
  "cost_total": 150.15015000000002,
  "ending_equity": 99789.25209321156
}
```

## Stability
```json
{
  "score_metric": "sharpe",
  "best_score": -6.283164192189335,
  "top_quantile_mean": -6.283164192189335,
  "top_quantile_threshold": -6.283164192189335,
  "neighbor_mean": -8.016903342654798,
  "neighbor_count": 3,
  "parameter_coverage": 0.75,
  "stability_status": "Review",
  "notes": "Stability cannot be confirmed because the score is weak, missing, or has too few neighboring parameters."
}
```

## Safety Boundary
Read-only replay-to-DataFrame research adapter; no live orders, broker calls, or market refresh.

## Missing Data Log
_None._
